from functools import reduce
from django import forms
from django.db import models, router
from django.core import exceptions
from django.conf import settings

from .querysetsequence import QuerySetSequence
from .utils import db_list_for_read, select_read_db

class ShardedForeignKey(models.ForeignKey):

    def __init__(self, to, on_delete, related_name=None, related_query_name=None,
                 limit_choices_to=None, parent_link=False, to_field=None,
                 db_constraint=True,db_for_read = None, **kwargs):# db_for_read = None, db_list_for_read = None, **kwargs):

        self.db_for_read = db_for_read
        self.db_list_for_read = None

        super(ShardedForeignKey, self).__init__(to, on_delete, related_name, related_query_name, limit_choices_to, parent_link, to_field, db_constraint, **kwargs)

        if not isinstance(to, str):
            self.db_list_for_read = db_list_for_read(model_name=str(self.remote_field.model._meta.verbose_name))       

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