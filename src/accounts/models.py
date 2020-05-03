from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from sharding.customizations import ShardedUser, ShardedModel
from sharding.fields import ShardedOneToOneField

from sharding.models import Databases
from sharding.utils import select_write_db
import uuid

class User(ShardedUser): 
    pass
    

class Profile(ShardedModel):

    user     = ShardedOneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=30, blank=True)

    def __str__(self):  # __unicode__ for Python 2
        return "%s profile's" % self.user.username

    def save(self, *args, **kwargs):

        
        super(Profile, self).save(*args, **kwargs)

        if hasattr(self._meta,"ShardedOneToOne"):
            
            for f in self._meta.ShardedOneToOne:
                print(self._state.db)
                pass
                # value_instance = getattr(self, f.verbose_name) 
                # #value_instance._state.db = us_db
                # pk = value_instance.pk
                # userq = User._base_manager.db_manager(us_db).get(pk = pk)
                # userq.delete()
                # #value_instance.delete()





@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # tell no must add try/except to avoid recreate 
        try:
            Profile.objects.create(user=instance)
        except:
            print("post_save: profile exist")
    # tell no must add try/except to avoid resave        
    try:
       instance.profile.save(user=instance)
    except:
        print("post_save: user exist")
    
    
