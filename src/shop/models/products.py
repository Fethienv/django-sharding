#import uuid
#from itertools import islice, chain
#from functools import reduce

from django import forms
from django.db import models#, Error, router
#from django.core import exceptions
#from django.conf import settings
from django.contrib.auth import get_user_model

from sharding.customizations import ShardedModel
from sharding.fields import ShardedForeignKey

user = get_user_model()

#from sharding.utils import db_list_for_read, select_read_db


class  Product(ShardedModel):
   
    name  = models.CharField(db_index=True, max_length=120)
    desc  = models.CharField(db_index=True, max_length=120)
    slug  = models.SlugField(db_index=True, unique=True )

    vendor = ShardedForeignKey(user, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Product"
