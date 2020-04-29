
from django.db import models, Error, router
from .models import Databases
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

# select wicth the right db for writing
def select_write_db(model_name):
    db_list = Databases.objects.all().filter(model_name=model_name)

    if db_list.count() == 0:
        raise Error(f"No database for {model_name} Model, please add it from admin")

    for db in db_list:
        if db.count < settings.DATABASE_MAX_ROWS:
            return db
    raise Error("Database full")

# get replica db list for ForeignKeyFiled or ManyToManyField
def db_list_for_read(model_name):

    try:
        db_list = Databases.objects.all().filter(model_name=model_name).exclude(count=0)

        if db_list.count() == 0:
            raise Error(f"No database for {model_name} Model, please add it from admin")

        return db_list
    except:
        return None

# select one replica read db
# not completed yet
def select_read_db(model_name = None, is_sharded = True):
    if model_name:
        db_list = Databases.objects.all().filter(model_name=model_name)

        if db_list.count() == 0:
            raise Error(f"No database for {model_name} Model, please add it from admin")

        if not is_sharded:
            return None

        # here select replica
        return model_name + '_1'   
        #return db_list
    return None