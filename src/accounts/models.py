from django.db import models
from django.db.models.signals import post_save, post_delete
from django.core.signals import request_finished
from django.dispatch import receiver



from sharding.customizations import ShardedUser, ShardedModel
from sharding.fields import ShardedOneToOneField

from sharding.models import Databases
from sharding.utils import select_write_db
import uuid

from django.contrib.contenttypes.models import ContentType

class User(ShardedUser): 
    pass
    


def cascade_delete(model):
    #@receiver(post_delete, sender=model)
    def delete_repo(sender, instance, **kwargs):
        print(instance, sender)

    request_finished.connect(delete_repo, sender=model)

    

    # if hasattr(instance._meta,"ShardedOneToOne"):
    #     for f in instance._meta.ShardedOneToOne:
    #         value_instance = getattr(instance, f.verbose_name) 
    #         #value_instance._state.db = us_db
    #         pk = value_instance.pk
    #         print(f.verbose_name, pk)
    #         ct_model = ContentType.objects.get(model=f.verbose_name).model_class()
    #         ct_model_obj = ct_model.objects.using(instance._state.db).get(pk=value_instance.pk)
    #         print(ct_model_obj.nid)
    #         ct_model_obj.db_for_write = instance._state.db
    #         print(instance._state.db)
    #         ct_model_obj.delete()

def CASCADE (model):
    return models.SET(cascade_delete(model))

class Profile(ShardedModel):

    user     = ShardedOneToOneField(User, on_delete=models.DO_NOTHING)
    location = models.CharField(max_length=30, blank=True)

    def __str__(self):  # __unicode__ for Python 2
        return "%s profile's" % self.user.username

    

    #     if hasattr(self._meta,"ShardedOneToOne"):
            
    #         for f in self._meta.ShardedOneToOne:
    #             value_instance = getattr(self, f.verbose_name) 
    #             #value_instance._state.db = us_db
    #             pk = value_instance.pk

    #             print(f.verbose_name, pk)


    #     super(Profile, self).delete()

    # def save(self, *args, **kwargs):

        
    #     super(Profile, self).save(*args, **kwargs)

    #     if hasattr(self._meta,"ShardedOneToOne"):
            
    #         for f in self._meta.ShardedOneToOne:
    #             print(self._state.db)
    #             pass
    #             # value_instance = getattr(self, f.verbose_name) 
    #             # #value_instance._state.db = us_db
    #             # pk = value_instance.pk
    #             # userq = User._base_manager.db_manager(us_db).get(pk = pk)
    #             # userq.delete()
    #             # #value_instance.delete()


# to complete
# @receiver(post_delete, sender=Profile)
# def delete_repo(sender, instance, **kwargs):
#     print(instance, sender)

#     if hasattr(instance._meta,"ShardedOneToOne"):
#         for f in instance._meta.ShardedOneToOne:
#             value_instance = getattr(instance, f.verbose_name) 
#             #value_instance._state.db = us_db
#             pk = value_instance.pk
#             print(f.verbose_name, pk)
#             ct_model = ContentType.objects.get(model=f.verbose_name).model_class()
#             ct_model_obj = ct_model.objects.using(instance._state.db).get(pk=value_instance.pk)
#             print(ct_model_obj.nid)
#             ct_model_obj.db_for_write = instance._state.db
#             print(instance._state.db)
#             ct_model_obj.delete()


# Done
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:  
        Profile.objects.create(user=instance)


    

    
    
