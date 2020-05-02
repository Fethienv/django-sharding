from django.db import models
from django.contrib.auth import get_user_model

from sharding.customizations import ShardedModel
from sharding.fields import ShardedForeignKey, ShardedManyToManyField

user = get_user_model()


class  NormalProductModel(models.Model):
    name  = models.CharField(db_index=True, max_length=120)
    desc  = models.CharField(db_index=True, max_length=120)
    slug  = models.SlugField(db_index=True, unique=True )

    SHAREDED_MODEL = False

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Normal product"

class  Product(ShardedModel):
   
    name  = models.CharField(db_index=True, max_length=120)
    desc  = models.CharField(db_index=True, max_length=120)
    slug  = models.SlugField(db_index=True, unique=True )

    vendor = ShardedForeignKey(user, on_delete=models.CASCADE, blank=True, null=True, db_constraint=False,)

    #vendor  = ShardedManyToManyField(user , db_constraint=False)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Product"
        #db_table = '"product_1-primary"."shop_product"'         # for all other backends
        managed = False
