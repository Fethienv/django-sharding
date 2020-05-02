from django.db import models
from django.contrib.auth import get_user_model

from sharding.customizations import ShardedModel
from sharding.fields import ShardedForeignKey, ShardedManyToManyField

from .products import Product,NormalProductModel
user = get_user_model() 




class  NormalStoreModel(models.Model):
    stores = models.CharField(db_index=True,max_length=36)
    products = models.ManyToManyField(NormalProductModel, db_index=True, db_constraint=False)

    def __str__(self):
        return self.stores
    
    class Meta:
        verbose_name = "Normal store"



class  Store(ShardedModel):
   
    name  = models.CharField(db_index=True, max_length=120)
    desc  = models.CharField(db_index=True, max_length=120)
    slug  = models.SlugField(db_index=True, unique=True )

    products  = ShardedManyToManyField( to = Product, db_constraint=False )
    #products = models.CharField(db_index=True, max_length=500) #ShardedForeignKey(ShardedManyToManyModel, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Store"


# class Store_lookupModel(ShardedModel):

#     stores   = ShardedForeignKey(Store, on_delete=models.CASCADE)
#     products = ShardedForeignKey(Product, on_delete=models.CASCADE)
