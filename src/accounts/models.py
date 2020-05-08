from django.db import models
from django.db.models.signals import post_save, post_delete
from django.core.signals import request_finished
from django.dispatch import receiver



from sharding.customizations import ShardedUser, ShardedModel, ShardUserModelQueryset
from sharding.fields import ShardedOneToOneField

from sharding.models import Databases
from sharding.utils import select_write_db
import uuid

from django.contrib.contenttypes.models import ContentType

class User(ShardedUser): 
    pass
    

class Profile(ShardedModel):

    owner     = ShardedOneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=30, blank=True)

    def __str__(self):  # __unicode__ for Python 2
        return "%s profile's" % self.owner.username

# Done
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:  
        Profile.objects.create(owner=instance)


    

    
    
