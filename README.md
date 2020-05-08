# django-sharding
Simple horizontal scaling utilities for django framework

- Short def:
    * Scalability is the property of a system to handle a growing amount of work by adding resources to the system
    * Scaling horizontally (out/in) means adding more nodes to (or removing nodes from) a system, such as adding a new computer to a distributed software application. An example might involve scaling out from one web server to three.
    * With horizontal-scaling it is often easier to scale dynamically by adding more machines into the existing pool


This simple package allows the developer to add more than one table to one Model, each table limited by the maximum rows specified in settings.py

<p align="center">
  <img width="460" height="300" src="https://camo.githubusercontent.com/3b865eebc64c4b1d31640c853ea76d25c7c894b6/68747470733a2f2f692e737461636b2e696d6775722e636f6d2f4f6e33744f2e706e67">
</p>

#### How django-sharding work?:
- Every Model has its own database and you can use 1 database for more than one model
- Every table has new id as premairy key (nid)
- nid is uuid but the first 8 charter are fixed and it used as prefix
- every prefix is specific to database key
- every database can spilt by row count max
- sharding django create a table for databases and register number of rows.

## Installation:
1. clone folder sharding and add it to settings.py in INSTALED_APPS or run

```
pip install django-horizontal-sharding
```

```
INSTALLED_APPS = [
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'sharding.apps.ShardingConfig',
    'accounts.apps.AccountsConfig',

    .....

]
```

2. add your databases and make sure the key of user database is user_1

```
DATABASES = {
    'default': { # 
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'default.sqlite3'),
        'USER': 'sqlite3_default',
        'PASSWORD': 'veryPriv@ate'
    },
    'user_1': { # range 1-100
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'accounts_1-primary.sqlite3'),
        'USER': 'sqlite3_shop',
        'PASSWORD': 'veryPriv@ate'
    },

    .....

}

```

Note: all keys should be in lower letters

3. add the following settings to settings.py:

```
DATABASE_MAX_ROWS = 100

DATABASE_ROUTERS = ['sharding.router.ShardingRouter', ]

USER_INIT_DATABASE = 'user_1' # must be the same user database key in DATABASES

SHARDING_USER_MODEL = True

FIXTURE_DIRS = ['sharding.fixtures',]
```

4. run makemigrations
```
python manage.py makemigrations
```
5. migrate all databases:
```
python manage.py migrate
python manage.py migrate --database=user_1

...

```

5. load fixtures
```
python manage.py loaddata --database=default user
python manage.py loaddata --database=user_1 user
```

6. create super user
```
python manage.py createsuperuser
```
7. run server

```
python manage.py runserver
```

8. login to admin site

## User guide:

### Step 1: 
whene admin site opened go to Databases and add all your datatbases 
- Note: 
1. model name field should be same as model, Note: name should be in lower letters
2. model name + _ + number field should be same as database key in settings.py

### Step 2:

1. To sharding model, you must inherit ShardedModel, it will automaticly change the id by new id base on uuid3 and uuid4
2. To use ForeignKey field you should import it from sharding.fields

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

3. To use ManyToMany field you should import it from sharding.fields

```
from django.db import models

from sharding.customizations import ShardedModel
from sharding.fields import ShardedManyToManyField

from .products import Product

class  Store(ShardedModel):
   
    name  = models.CharField(db_index=True, max_length=120)
    desc  = models.CharField(db_index=True, max_length=120)
    slug  = models.SlugField(db_index=True, unique=True )

    products  = ShardedManyToManyField( to = Product, db_constraint=False )

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Store"

```

4. To use OneToOne field you should import it from sharding.fields

```
from django.db import models

from django.db.models.signals import post_save
from django.dispatch import receiver

from sharding.customizations import ShardedModel
from sharding.fields import ShardedOneToOneField

User = get_user_model()

class Profile(ShardedModel):

    owner     = ShardedOneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=30, blank=True)

    def __str__(self):  # __unicode__ for Python 2
        return "%s profile's" % self.owner.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:  
        Profile.objects.create(owner=instance)

```

### Step 3:
1. To sharding users, you must inherit ShardedUser, it will automaticly change the id by new id base on uuid3 and uuid4, then add AUTH_USER_MODEL = 'accounts.User' to settings.py

Exemple:
```
from sharding.customizations import ShardedUser

class User(ShardedUser): 
    pass
    
```

2. add sharded forms to form.py

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

3. add ShardedUserAdminModel to admin.py


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


### TO DO:
- Add more related Fileds.
- multithreading for loops
- add mange.py command to auto insert databases names in default database and dump fixtures (python manage.py load_shard_dbs) 
- Add on_delete = CASCADE To ShardedForeignKeyField

### Contribute:
- Check for open issues or open a fresh issue to start a discussion around a feature idea or a bug.
- Fork the repository on GitHub to start making your changes.
- Write a test which shows that the bug was fixed or that the feature works as expected.
- Send a pull request and bug the maintainer until it gets merged and published

