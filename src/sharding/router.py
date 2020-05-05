import random
from django.conf import settings
from django.db import Error

from .models import Databases
from .utils import select_write_db


class ShardingRouter:

    route_excluded_app_labels = [] 
    route_app_labels = ['store']


    def db_for_read(self, model, **hints):
        """
        Reads go to a randomly-chosen replica.
        """

        # model_name = str(model._meta.model_name).split("_")[0]
        # print(model_name)
        
        # if model_name == "store":
        #     #return "store_1"
        #     print("store_1")
        # elif model_name == "product":#in self.route_app_labels:
        #     #return  'product_1'
        #     print("product_1")
        return  'default' #random.choice(['replica1', 'replica2']) 

    def db_for_write(self, model, **hints):
        """
        Writes always go to primary.
        """
        #if model._meta.app_label in self.route_app_labels:
        if hasattr(model, "using_db") and model.using_db is not None:

            return  model.using_db
        
        if hasattr(model, "db_for_write") and model.db_for_write is not None:
            print("router hasattr: ", model, model.db_for_write)
            return  model.db_for_write

        model_name    = str(model._meta.model_name).split("_")[0]

        try:
            db = select_write_db(model_name = model_name)
            print("roouter select_write_db: ",model, str(db))
            return str(db)
        except:
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