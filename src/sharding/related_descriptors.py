
from django.db.models.fields.related_descriptors import (
    ForeignKeyDeferredAttribute, ForwardManyToOneDescriptor,
    ForwardOneToOneDescriptor, ManyToManyDescriptor,
    ReverseManyToOneDescriptor, ReverseOneToOneDescriptor,
)
from django.contrib.contenttypes.models import ContentType

from .utils import db_list_for_read, select_read_db,select_write_db

class ShardForwardManyToOneDescriptor(ForwardManyToOneDescriptor):
    def get_queryset(self, **hints):
        return self.field.remote_field.model.objects.db_manager(hints=hints).all()

#class ShardReverseManyToOneDescriptor(ReverseManyToOneDescriptor):


class ShardForwardOneToOneDescriptor(ForwardOneToOneDescriptor):
    """
    Accessor to the related object on the forward side of a one-to-one relation.

    In the example::

        class Restaurant(Model):
            place = OneToOneField(Place, related_name='restaurant')

    ``Restaurant.place`` is a ``ForwardOneToOneDescriptor`` instance.
    """

    def get_queryset(self, **hints):
        return self.field.remote_field.model.objects.db_manager(hints=hints).all()

    # def _get_object(self, instance):
    #     qs = self.get_queryset(instance=instance)
    #     # Assuming the database enforces foreign keys, this won't fail.
    #     qss = qs.get(self.field.get_reverse_related_filter(instance))
    #     return qss

    # def get_object(self, instance):
    #     if self.field.remote_field.parent_link:
    #         deferred = instance.get_deferred_fields()
    #         # Because it's a parent link, all the data is available in the
    #         # instance, so populate the parent model with this data.
    #         rel_model = self.field.remote_field.model
    #         fields = [field.attname for field in rel_model._meta.concrete_fields]

    #         # If any of the related model's fields are deferred, fallback to
    #         # fetching all fields from the related model. This avoids a query
    #         # on the related model for every deferred field.
    #         if not any(field in fields for field in deferred):
    #             kwargs = {field: getattr(instance, field) for field in fields}
    #             obj = rel_model(**kwargs)
    #             obj._state.adding = instance._state.adding
    #             obj._state.db = instance._state.db
    #             return obj
    #     obj = self._get_object(instance)
    #     print(obj)
    #     return obj

    def __set__(self, instance, value):
        super(ShardForwardOneToOneDescriptor, self).__set__(instance, value)
        
        # db = select_write_db(model_name=instance.__class__._meta.model_name)
        # # save the same value instance on the same field then delete after
        # ct_model = ContentType.objects.get(model=value.__class__._meta.verbose_name).model_class()
        # ct_model.db_for_write = str(db)
        # ct_model_obj = ct_model.objects.filter(pk=value.pk)
        # ct_model.db_for_write = None
        
        # try:
        # #     #if ct_model_obj.count() == 0:
                     
        #     value.save(using=str(db)) 
        # #     #else:
        # #         #pass
        # except:
        #     print("exist")

        #try:    
        
        #except:
            #pass
        



class ShardReverseOneToOneDescriptor(ReverseOneToOneDescriptor):
    def get_queryset(self, **hints):
        return self.related.related_model.objects.db_manager(hints=hints).all()

    def __set__(self, instance, value):
        print("set")
        return super(ShardReverseOneToOneDescriptor, self).__set__(instance, value)

    


################# ManyToManyDescriptor
# from django.utils.functional import cached_property



# class CustomManyToManyDescriptor(ManyToManyDescriptor): 


#     def __init__(self, rel, reverse=False):
#         super(CustomManyToManyDescriptor, self).__init__(rel, reverse)

#     @cached_property
#     def related_manager_cls(self):
#         related_model = self.rel.related_model if self.reverse else self.rel.model

#         #return create_forward_many_to_many_manager(
#         forward = create_forward_many_to_many_manager(
#             related_model._default_manager.__class__,
#             self.rel,
#             reverse=self.reverse,
#             using_db= 'product_1'
#         )
#         print("related_model", related_model)
#         return forward
