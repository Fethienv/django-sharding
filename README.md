# django-sharding
Simple horizontal scaling utilities for django framework


## Installations:
- clone folder sharding and add it to settings.py in INSTALED_APPS
- add your databases and make sure the key of user database is user_1
- add the following settings to settings.py:

DATABASE_MAX_ROWS = 100

DATABASE_ROUTERS = ['sharding.router.ShardingRouter', ]

USER_INIT_DATABASE = 'user_1' # must be the same user database key in DATABASES

SHARDING_USER_MODEL = True

FIXTURE_DIRS = ['sharding.fixtures',]

## Use guide:

### Step 1: 
Open admin site go to Databases and add all your datatbases 
Note: 
1- model name field should be same as model
2- model name + _ + number field should be same as database key in settings.py

### Step 2:

1- To sharding model, you must inihrite ShardedModel, it will automaticly change the id by new id base on uuid3 and uuid4
2- To use ForeignKey field you should import it from sharding.fields

Exemple:
```
from django import forms
from django.db import models
from django.contrib.auth import get_user_model

from sharding.customizations import ShardedModel
from sharding.fields import ShardedForeignKey

user = get_user_model()

class  Product(ShardedModel):
  
    name  = models.CharField(db_index=True, max_length=120)
    desc  = models.CharField(db_index=True, max_length=120)
    slug  = models.SlugField(db_index=True, unique=True )

    vendor = ShardedForeignKey(
        user,
        on_delete=models.DO_NOTHING,
        db_constraint=False,  # May be using anothor database
        #db_for_read=None , # if single database for read
    )

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Product"

```

### Step 3:
1- To sharding users, you must inihrite ShardedUser, it will automaticly change the id by new id base on uuid3 and uuid4, then add AUTH_USER_MODEL = 'accounts.User' to settings.py

Exemple:
```
from sharding.customizations import ShardedUser

class User(ShardedUser): 
    pass
    
```

2- add sharded forms to form.py

Exemple:
```
from django import forms
from sharding.forms import ShardedUserRegisterForm, ShardedUserAdminCreationForm, ShardedUserAdminChangeForm
from .models import User


class RegisterForm(ShardedUserRegisterForm):
    pass

class UserAdminCreationForm(ShardedUserAdminCreationForm):
    pass

class UserAdminChangeForm(ShardedUserAdminChangeForm):
    pass


```    

3- add ShardedUserAdminModel to admin.py


Exemple:
```
from django.contrib import admin, auth

from django.contrib.auth.models import Group
from sharding.admin_customizations import ShardedUserAdminModel

User = auth.get_user_model()

class UserAdmin(ShardedUserAdminModel):
    pass

admin.site.register(User, UserAdmin)

```

That's all 

