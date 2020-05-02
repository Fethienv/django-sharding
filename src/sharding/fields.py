from functools import reduce
from functools import partial
from django import forms
from django.db import models, router

from django.db.models.fields.related import lazy_related_operation,resolve_relation

from django.db.models.fields.related_descriptors import ManyToManyDescriptor

from django.db.models.utils import make_model_tuple
from django.db.models.deletion import CASCADE, SET_DEFAULT, SET_NULL
from django.core import exceptions
from django.conf import settings

from django.utils.translation import gettext_lazy as _
from .querysetsequence import QuerySetSequence
from .utils import db_list_for_read, select_read_db,select_write_db
from .customizations import ShardedModel, many_to_manyManager,many_to_many_save

from .models import Databases
import uuid

class ShardedForeignKey(models.ForeignKey):

    def __init__(self, to, on_delete, related_name=None, related_query_name=None,
                 limit_choices_to=None, parent_link=False, to_field=None,
                 db_constraint=True,db_for_read = None, **kwargs):

        self.db_for_read = db_for_read
        self.db_list_for_read = None

        super(ShardedForeignKey, self).__init__(to=to, on_delete=on_delete, related_name=related_name, related_query_name=related_query_name, limit_choices_to=limit_choices_to, parent_link=parent_link, to_field=to_field, db_constraint=db_constraint, **kwargs)

        if not isinstance(to, str):
            if self.remote_field.model.SHAREDED_MODEL:
                self.db_list_for_read = db_list_for_read(model_name=str(self.remote_field.model._meta.verbose_name).lower())
            else:
                self.db_list_for_read = None       

    def validate(self, value, model_instance):

        if self.remote_field.parent_link:
            return
        super(models.ForeignKey,self).validate(value, model_instance)

        if value is None:
            return

        if self.db_list_for_read:
            state = {}
            i = 0
            for db in self.db_list_for_read:
                i += 1
                using = db.get_name
                qs = self.remote_field.model._default_manager.using(using).filter(**{self.remote_field.field_name: value})
                qs = qs.complex_filter(self.get_limit_choices_to())
                if not qs.exists():
                    state[i] = False
                else:
                    state[i] = True

            if not True in state.values():
               raise exceptions.ValidationError(
                    self.error_messages['invalid'],
                    code='invalid',
                    params={
                        'model': self.remote_field.model._meta.verbose_name, 'pk': value,
                        'field': self.remote_field.field_name, 'value': value,
                    },      # 'pk' is included for backwards compatibility
                ) 
        else:
            if self.db_for_read:
                using = self.db_for_read
            else:
                using = router.db_for_read(self.remote_field.model, instance=model_instance)

            qs = self.remote_field.model._default_manager.using(using).filter(
                **{self.remote_field.field_name: value}
            )
            qs = qs.complex_filter(self.get_limit_choices_to())
            if not qs.exists():
                raise exceptions.ValidationError(
                    self.error_messages['invalid'],
                    code='invalid',
                    params={
                        'model': self.remote_field.model._meta.verbose_name, 'pk': value,
                        'field': self.remote_field.field_name, 'value': value,
                    },      # 'pk' is included for backwards compatibility
                )
    
    def formfield(self, *, using=None, **kwargs):

        if not hasattr(self.model._meta,"ShardedForeignKey"):
            self.model._meta.ShardedForeignKey = []
        self.model._meta.ShardedForeignKey.append(self) 

        if isinstance(self.remote_field.model, str):
            raise ValueError("Cannot create form field for %r yet, because "
                             "its related model %r has not been loaded yet" %
                             (self.name, self.remote_field.model))

        if self.db_list_for_read and self.db_list_for_read.count() != 0 and self.remote_field.model.SHAREDED_MODEL: 
                queryset = reduce(QuerySetSequence, [self.remote_field.model._default_manager.raw_queryset().using(db.get_name) for db in self.db_list_for_read]) 
        else:
            if self.db_for_read:
                using = self.db_for_read
            else:
                using = using

            queryset = self.remote_field.model._default_manager.using(using)

        kwargs['queryset'] = queryset
        field = super(models.ForeignKey,self).formfield(**{
            'form_class': forms.ModelChoiceField,
            'queryset': queryset,
            'to_field_name': self.remote_field.field_name,
            **kwargs,
        })
        return field





def save_method(self, *args, **kwargs):
    if self.SHAREDED_MODEL:
        print("in model save - self: ", self)

        print("in model save - args: ", args)
        print("in model save - kwargs: ", kwargs)

        # select database name
        db = select_write_db(model_name=self._meta.model_name)
        print("in model save - db: ", db)

        # get prefix
        prefix = db.get_prefix
        print("in model save - prefix: ", prefix)
        if self.nid:
            print("in model save - self.nid exist: ", self.nid)
            # get prefix
            prefix = str(self.nid)[:8]
            print("in model save - prefix form nid: ", prefix)
            # get database name
            db_name = Databases.objects.get_data_by_prefix(prefix)
            print("in model save - db_name form nid: ", db_name)
            # save
            #Product
            if not self.db_for_write:
                super().save(*args, **kwargs, using=str(db_name))
            else:
                super().save(*args, **kwargs, using=str(self.db_for_write))
        else:
            # create nid
            self.nid = str(prefix)+ "-" + str(uuid.uuid4())[9:]
            print("in model save - self.nid: ", self.nid)

            # write to selected database 
            if not self.db_for_write:
                super().save(*args, **kwargs, using=str(db.get_name))
                # update count
                db.count = db.count + 1
                db.save()
            else:
                super().save(*args, **kwargs, using=str(self.db_for_write))
                
    else:
        if not self.db_for_write:
            super().save(*args, **kwargs) 
        else:
            super().save(*args, **kwargs, using=str(self.db_for_write))

def get_lists(self):
    return self.product_id


def create_Sharded_many_to_many_intermediary_model(field, klass):
    from django.db import models

    def set_managed(model, related, through):
        through._meta.managed = model._meta.managed or related._meta.managed

    to_model = resolve_relation(klass, field.remote_field.model)
    name = '%s_%s' % (klass._meta.object_name, field.name)
    lazy_related_operation(set_managed, klass, to_model, name)

    to = make_model_tuple(to_model)[1]
    from_ = klass._meta.model_name
    if to == from_:
        to = 'to_%s' % to
        from_ = 'from_%s' % from_

    meta = type('Meta', (), {
        'db_table': field._get_m2m_db_table(klass._meta),
        'auto_created': klass,
        'app_label': klass._meta.app_label,
        'db_tablespace': klass._meta.db_tablespace,
        'unique_together': (from_, to),
        'verbose_name': _('%(from)s-%(to)s relationship') % {'from': from_, 'to': to},
        'verbose_name_plural': _('%(from)s-%(to)s relationships') % {'from': from_, 'to': to},
        'apps': field.model._meta.apps,
    })


    if hasattr(klass, "_state") or hasattr(klass, "db"):
        many_to_manyManager.data_name = klass._state.db or klass.db
    else:
        many_to_manyManager.data_name = None

    print(from_, to)

    # Construct and return the new class.
    new_class = type(name, (models.Model,), {
    #new_class = type(name, (ShardedModel,), {
        'Meta': meta,
        '__module__': klass.__module__,
        #'nid': models.CharField(db_index=True, editable=False, max_length=36, unique=True, primary_key=True),
        from_: models.ForeignKey(
            klass,
            related_name='%s+' % name,
            db_tablespace=field.db_tablespace,
            db_constraint=field.remote_field.db_constraint,
            on_delete=CASCADE,
        ),
        to: models.ForeignKey(
            to_model,
            related_name='%s+' % name,
            db_tablespace=field.db_tablespace,
            db_constraint=field.remote_field.db_constraint,
            on_delete=CASCADE,
        ),
        'objects':many_to_manyManager(),
        'SHAREDED_MODEL':True,
        '__str__':get_lists,
        #'save':many_to_many_save,
       
    })
    #print("new_class", new_class)
    return new_class

class ShardedManyToManyField(models.ManyToManyField):


    def __init__(self, to,lookup_model=None, db_for_read=None, related_name=None, related_query_name=None,
                 limit_choices_to=None, symmetrical=None, through=None,
                 through_fields=None, db_constraint=True, db_table=None,
                 swappable=True, **kwargs):

        super(ShardedManyToManyField, self).__init__(to=to, related_name=related_name, related_query_name=related_query_name, limit_choices_to=limit_choices_to, symmetrical=symmetrical, through=through,
                                                     through_fields= through_fields, db_constraint=db_constraint, db_table = db_table, swappable= swappable, **kwargs)

        self.db_for_read = db_for_read
        self.db_list_for_read = None
        self.remote_model = to
        self.lookup_model = lookup_model

        if not isinstance(to, str):         
            if self.remote_model.SHAREDED_MODEL:
                self.db_list_for_read = db_list_for_read(model_name=str(self.remote_model._meta.verbose_name).lower())
            else:
                self.db_list_for_read = None 

    def value_from_object(self, obj):
        db_name = obj._state.db
        remote_field = self.remote_model
        remote_field_name = str(remote_field).split(".")
        db_table        = str(self.model._meta.app_label.lower())+"_"+str(self.model._meta.verbose_name.lower())+"_"+str(remote_field_name[2])
        where_colomn    = str(self.model._meta.verbose_name.lower()) + '_id'
        fetech_colomn   = str(remote_field._meta.verbose_name.lower()) + '_id'
        selected        = obj.__class__.objects.my_custom_sql(db_name, db_table, fetech_colomn, where_colomn, obj.nid)
        return [nid[fetech_colomn] for nid in selected]
        #return[] if obj.pk is None else list(getattr(obj, self.attname).all())

    def formfield(self, *, using=None, **kwargs):
        if not hasattr(self.model._meta,"ShardedManyToManyField"):
            self.model._meta.ShardedManyToManyField = []
        self.model._meta.ShardedManyToManyField.append(self.remote_model) 

        if self.db_list_for_read and self.db_list_for_read.count() != 0 and self.remote_model.SHAREDED_MODEL: 
                queryset = reduce(QuerySetSequence, [self.remote_model._default_manager.raw_queryset().using(db.get_name) for db in self.db_list_for_read]) 
        else:
            if self.db_for_read:
                using = self.db_for_read
            else:
                using = using

            queryset = self.remote_model._default_manager.using(using)

        defaults = {
            'form_class': forms.ModelMultipleChoiceField,
            'queryset': queryset,
            **kwargs,
        }

        # If initial is passed in, it's a list of related objects, but the
        # MultipleChoiceField takes a list of IDs.
        if defaults.get('initial') is not None:
            initial = defaults['initial']
            if callable(initial):
                initial = initial()
            defaults['initial'] = [i.pk for i in initial]

        return super(models.ManyToManyField, self).formfield(**defaults)

    def contribute_to_class(self, cls, name, **kwargs):
        # To support multiple relations to self, it's useful to have a non-None
        # related name on symmetrical relations for internal reasons. The
        # concept doesn't make a lot of sense externally ("you want me to
        # specify *what* on my non-reversible relation?!"), so we set it up
        # automatically. The funky name reduces the chance of an accidental
        # clash.
        if self.remote_field.symmetrical and (
                self.remote_field.model == "self" or self.remote_field.model == cls._meta.object_name):
            self.remote_field.related_name = "%s_rel_+" % name
        elif self.remote_field.is_hidden():
            # If the backwards relation is disabled, replace the original
            # related_name with one generated from the m2m field name. Django
            # still uses backwards relations internally and we need to avoid
            # clashes between multiple m2m fields with related_name == '+'.
            self.remote_field.related_name = "_%s_%s_+" % (cls.__name__.lower(), name)

        super(models.ManyToManyField, self).contribute_to_class(cls, name, **kwargs)

        # The intermediate m2m model is not auto created if:
        #  1) There is a manually specified intermediate, or
        #  2) The class owning the m2m field is abstract.
        #  3) The class owning the m2m field has been swapped out.
        if not cls._meta.abstract:
            if self.remote_field.through:
                def resolve_through_model(_, model, field):
                    field.remote_field.through = model
                lazy_related_operation(resolve_through_model, cls, self.remote_field.through, field=self)
            elif not cls._meta.swapped:
                self.remote_field.through = create_Sharded_many_to_many_intermediary_model(self, cls)

        # Add the descriptor for the m2m relation.
        setattr(cls, self.name, ManyToManyDescriptor(self.remote_field, reverse=False))

        # Set up the accessor for the m2m table name for the relation.
        self.m2m_db_table = partial(self._get_m2m_db_table, cls._meta)


#Class on_delete