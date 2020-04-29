from django.db import models
from django.contrib.auth import get_user_model

from sharding.customizations import ShardedModel
from sharding.fields import ShardedForeignKey, ShardedManyToManyField

from .products import Product
user = get_user_model() 


class  Store(ShardedModel):
   
    name  = models.CharField(db_index=True, max_length=120)
    desc  = models.CharField(db_index=True, max_length=120)
    slug  = models.SlugField(db_index=True, unique=True )

    products = ShardedManyToManyField(Product, db_constraint=False, blank=True)
    vendor   = ShardedForeignKey(user, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Store"