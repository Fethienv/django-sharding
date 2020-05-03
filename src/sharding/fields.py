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
from .customizations import ShardedModel, many_to_manyManager
from .related_descriptors import ShardReverseOneToOneDescriptor, ShardForwardOneToOneDescriptor

from .models import Databases

############################### ShardedForeignKey ################################
class ShardedForeignKey(models.ForeignKey):

    def __init__(self, to, on_delete, related_name=None, related_query_name=None,
                 limit_choices_to=None, parent_link=False, to_field=None,
                 db_constraint=False,db_for_read = None, **kwargs):

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




############################### ShardedManyToMany ################################
def get_lists(self):
    return self.product_id

class CModelState(object):
    """
    A class for storing instance state
    """
    def __init__(self, db=None):
        self.db = db
        # If true, uniqueness validation checks will consider this a new, as-yet-unsaved object.
        # Necessary for correct validation of new instances of objects with explicit (non-auto) PKs.
        # This impacts validation only; it has no effect on the actual save.
        self.adding = True

def create_Sharded_many_to_many_intermediary_model(field, klass,  db=None):
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

    # Construct and return the new class.
    new_class = type(name, (models.Model,), {
        'Meta': meta,
        '__module__': klass.__module__,
        from_: models.ForeignKey(
            klass,
            related_name='%s+' % name,
            db_tablespace=field.db_tablespace,
            db_constraint=field.remote_field.db_constraint,
            on_delete=CASCADE,
        ),
        to: models.ForeignKey(
            to_model,
            related_name= '%s+' % name,
            db_tablespace=field.db_tablespace,
            db_constraint=field.remote_field.db_constraint,
            on_delete=CASCADE,
        ),
        'objects':many_to_manyManager(),
        '__str__':get_lists,
        'using_db':db,
       
    })
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

    def formfield(self, *, using=None, **kwargs):
        if not hasattr(self.model._meta,"ShardedManyToManyField"):
            self.model._meta.ShardedManyToManyField = []
        if self.remote_model not in self.model._meta.ShardedManyToManyField:
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
                using_db = self.db_list_for_read.first().get_name if self.db_list_for_read else None

                self.remote_field.through = create_Sharded_many_to_many_intermediary_model(self, cls, db=using_db)

        # Add the descriptor for the m2m relation.
        #print(CustomManyToManyDescriptor(self.remote_field, reverse=False))
        setattr(cls, self.name, ManyToManyDescriptor(self.remote_field, reverse=False))

        # Set up the accessor for the m2m table name for the relation.
        self.m2m_db_table = partial(self._get_m2m_db_table, cls._meta)

############################### OneToOneField ################################

class ShardedOneToOneField(models.OneToOneField):

    related_accessor_class = ShardReverseOneToOneDescriptor
    forward_related_accessor_class = ShardForwardOneToOneDescriptor

    def __init__(self, to, on_delete, to_field=None, db_for_read=None, **kwargs):

        #kwargs['unique'] = True
        self.db_for_read = db_for_read

        super(ShardedOneToOneField, self).__init__(to, on_delete, to_field=to_field, **kwargs)

        if not isinstance(to, str):
            if self.remote_field.model.SHAREDED_MODEL:
                self.db_list_for_read = db_list_for_read(model_name=str(self.remote_field.model._meta.verbose_name).lower())
            else:
                self.db_list_for_read = None

    
    def formfield(self, **kwargs):
        if self.remote_field.parent_link:
            return None
        else:
            if not hasattr(self.model._meta,"ShardedOneToOne"):
                self.model._meta.ShardedOneToOne = []
            
            if self not in self.model._meta.ShardedOneToOne:
            #self.model._meta.ShardedManyToManyField.append(self.remote_model) 
                self.model._meta.ShardedOneToOne.append(self) 

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

    # def save_form_data(self, instance, data):

    #     help(self)

    #     print(" -------- save_form_data ------------- ",)
    #     print("data",data)
    #     print("instance",instance)
        
    #     pass

    #     # if isinstance(data, self.remote_field.model):
    #     #     #setattr(instance, self.name, data)
    #     #     print (self.remote_field.model,instance, self.name, data)
    #     # else:
    #     #     #setattr(instance, self.attname, data)
    #     #     print (self.remote_field.model, instance, self.name, data)
    #     #     # Remote field object must be cleared otherwise Model.save()
    #     #     # will reassign attname using the related object pk.
    #     #     #if data is None:
    #     #         #setattr(instance, self.name, data)
    

    # need to modify descreptor
    # def contribute_to_related_class(self, cls, related):

    #     if related.related_model._meta.verbose_name == "profile":
    #         print("reverse related: ", related)
    #         print("reverse related verbose_name: ", related.related_model._meta.verbose_name)
    #         print("reverse cls: ", cls)
    #         print("reverse cls._meta.concrete_model: ", cls._meta.concrete_model)
    #         print("related.get_accessor_name: ", related.get_accessor_name())
    #         print("related.get_accessor_name: ", self.related_accessor_class(related))
       
    #     # Internal FK's - i.e., those with a related name ending with '+' -
    #     # and swapped models don't get a related descriptor.
       
    #     if not self.remote_field.is_hidden() and not related.related_model._meta.swapped:
    #         setattr(cls._meta.concrete_model, related.get_accessor_name(), self.related_accessor_class(related))
    #         # While 'limit_choices_to' might be a callable, simply pass
    #         # it along for later - this is too early because it's still
    #         # model load time.
    #         if self.remote_field.limit_choices_to:
    #             cls._meta.related_fkey_lookups.append(self.remote_field.limit_choices_to)



#Class on_delete