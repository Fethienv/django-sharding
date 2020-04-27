import random
from utils.models import Databases
from django.conf import settings
from django.db import Error

def select_write_db(model_name):
    db_list = Databases.objects.all().filter(model_name=model_name)
    if db_list.count() == 0:
        raise Error(f"Database for {model_name} model dosen't exist")

    for db in db_list:
        if db.count < settings.DATABASE_MAX_ROWS:
            return str(db)
    raise Error("Database full")

def select_read_db(model_name):
    db_list = Databases.objects.all().filter(model_name=model_name)
    for db in db_list:
        if db.count < settings.DATABASE_MAX_ROWS:
            return db
    raise Error("Database full")


class accountsRouter:

    # route_app_labels = ['accounts',]
    #excluded_models = ["databases", 'logentry',"permission"] 

    # def db_for_read(self, model, **hints):
    #     """
    #     Reads go to a randomly-chosen replica.
    #     """
    #     return random.choice(['replica1', 'replica2'])

    

    # def db_for_write(self, model, **hints):
    #     """
    #     Writes always go to primary.
    #     """
    #     if model._meta.app_label in self.route_app_labels:
    #         return select_write_db(model._meta.model_name)
    #     return  'default'
        

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the primary/replica pool.
        """
        # db_list = Databases.objects.all()
        # db_obj1 = False
        # db_obj2 = False
        # for db in db_list:
        #     if obj1._state.db == str(db):
        #         db_obj1 = True

        #     if obj2._state.db == str(db):
        #         db_obj2 = True
        
        # if db_obj1 and db_obj2:
        #     return True
        # if obj1._state.db in db_list and obj2._state.db in db_list:
        #     return True
        return True

    # def allow_migrate(self, db, app_label, model_name=None, **hints):
    #     """
    #     All non-auth models end up in this pool.
    #     """
    #     return True