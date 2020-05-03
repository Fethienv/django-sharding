
from django.db.models.fields.related_descriptors import (
    ForeignKeyDeferredAttribute, ForwardManyToOneDescriptor,
    ForwardOneToOneDescriptor, ManyToManyDescriptor,
    ReverseManyToOneDescriptor, ReverseOneToOneDescriptor,
)
from django.contrib.contenttypes.models import ContentType

class ShardForwardOneToOneDescriptor(ForwardOneToOneDescriptor):

    def get_queryset(self, **hints):
        #return self.field.remote_field.model._base_manager.db_manager(hints=hints).all()
        return self.field.remote_field.model.objects.db_manager(hints=hints).all()

    def __set__(self, instance, value):
        super(ShardForwardOneToOneDescriptor, self).__set__(instance, value)
        # save the same value instance on the same field then delete after
        try:
            value.save(using=instance._state.db) 
        except:
            print("Descriptor, user exist")
        



class ShardReverseOneToOneDescriptor(ReverseOneToOneDescriptor):
    def get_queryset(self, **hints):
        #print(self.related.related_model._base_manager.db_manager(hints=hints).all())
        #print(self.related.related_model.objects.db_manager(hints=hints).all())
        #return self.related.related_model._base_manager.db_manager(hints=hints).all()
        return self.related.related_model.objects.db_manager(hints=hints).all()
    


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
