
from sharding.customizations import ShardedModel
from sharding.fields import ShardedForeignKey, ShardedManyToManyField
from .stores import Store
from .products import Product

class ShardedManyToManyModel(ShardedModel):

    store = ShardedForeignKey(Store, on_delete=models.CASCADE, blank=True, null=True)
    product = ShardedForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)