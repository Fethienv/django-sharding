import random
from django.conf import settings
from django.db import Error

from .models import Databases
from .utils import select_write_db


class ShardingRouter:

    route_excluded_app_labels = [] 
    route_app_labels = ['accounts','products']

    def db_for_read(self, model, **hints):
        """
        Reads go to a randomly-chosen replica.
        """
        #if model._meta.app_label in self.route_app_labels:
            #return select_write_db(model._meta.model_name)
        return 'default' #random.choice(['replica1', 'replica2']) 

    def db_for_write(self, model, **hints):
        """
        Writes always go to primary.
        """
        if model._meta.app_label in self.route_app_labels:
            return select_write_db(model._meta.model_name)

        return  'default'
        

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the primary/replica pool.
        """
        db_list = Databases.objects.all()
        db_obj1_list = db_list.filter(model_name= obj1._state.db.split("_")[0])
        db_obj2_list = db_list.filter(model_name= obj2._state.db.split("_")[0])
        if (db_obj1_list !=0 or obj1._state.db == "default") and (db_obj2_list !=0 or obj2._state.db == "default"):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        All non-auth models end up in this pool.
        """
        return True