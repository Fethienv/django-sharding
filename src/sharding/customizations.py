
import uuid
from functools import reduce

from django.db import models, Error, IntegrityError

from django.utils import timezone
from django.conf import settings

from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)

from .querysetsequence import QuerySetSequence
from .multidbquery import MultiDBQuerySet

from .models import Databases
from .utils import select_write_db
from django.db.models.deletion import Collector
from django.contrib.contenttypes.models import ContentType


class ShardUserModelQueryset(models.QuerySet):

    def delete(self):
        print("deleting ...") # debug
        count = self.count()
        for instance in self:
            
            print("get instance ...") # debug
            print(instance)
            instance_db = instance._state.db
            self_pk = instance.pk
            db = Databases.objects.get_data_by_full_name(instance._state.db)
            db.count = db.count - 1
            db.save()

            if instance.__class__.forward_models is not None:
                print("forward_fields", instance.__class__.forward_fields) # debug
                print("forward_models", instance.__class__.forward_models) # debug
                frd_pks = {}
                for forward_model in instance.__class__.forward_models:
                    attrname = instance.__class__.forward_fields[forward_model._meta.model_name]
                    frd_pks[getattr(instance, attrname + '_id')] = forward_model

            # 1- delete instance from its used database
            super(ShardUserModelQueryset,self).delete()

            # 2- same instance from related database:
            # forward_model ---> this instance
            if instance.__class__.forward_models is not None:
                for frd_pk in frd_pks:
     
                    forward_model = frd_pks[frd_pk]

                    print("forward model:", frd_pk, forward_model) # debug

                    ct_model = ContentType.objects.get(model=forward_model._meta.model_name).model_class()
                    ct_model_obj = ct_model.objects.filter(pk= frd_pk)

                    print("forward obj:", ct_model_obj) # debug

                    # do not delete forward_model instance if exist in its specific database
                    
                    if ct_model_obj.count() == 0:
                        qs = models.QuerySet(forward_model, using=str(instance_db)).filter(pk= frd_pk)
                        print(qs)           
                        collector = Collector(using=instance_db)
                        collector.collect(qs)
                        deleted, _rows_count = collector.delete()

            # 3- delete related model instance
            # related_model   --->    instance related to this model
            if instance.__class__.related_models is not None:
                print("get query set ...") # debug

                print("related models", instance.__class__.related_models) # debug
                

                for related_model in instance.related_models:
                    print("related fields", instance.related_fields[related_model._meta.model_name]) # debug

                    # get related database
                    db_list = Databases.objects.all().filter(model_name=related_model._meta.model_name).exclude(count=0)  
                    # if exist
                    if db_list.count() != 0:
                        for db in db_list:
                            #try: 

                                filters = {}
                                filters[instance.related_fields[related_model._meta.model_name]] = instance

                                qs1 = models.QuerySet(related_model, using=str(db)).filter(**filters)

                                # on delete cascad delete related instances
                                if self.model.on_delete[related_model._meta.model_name].__name__ == "CASCADE":

                                    collector = Collector(using=qs1.db)
                                    collector.collect(qs1)
                                    deleted, _rows_count = collector.delete()

                                if qs1.count() == 0:
                                    # if related instance dosn't exist
                                    # delete this model instance in other model databases 
                                    print("self_pk ", self_pk)
                                    qs2 = models.QuerySet(self.model, using=str(qs1.db)).filter(pk= self_pk)
                                    print('qs2', qs2)           
                                    collector = Collector(using=qs1.db)
                                    collector.collect(qs2)
                                    deleted, _rows_count = collector.delete()


 
################# User model ############################
class  ShardedUserManager(BaseUserManager):

    def create_user(self, username, email, password=None, is_staff =False, is_superuser = False):
        """
        Creates and saves a User with the given email and password.
        """
        print("create_user:", "creating .....")
        if not email:
            raise ValueError('Users must have an email address')

        # get prefix    
        try:
            db = select_write_db(model_name=self.model._meta.model_name)
            prefix = db.get_prefix 
        except:
            uuid3  = uuid.uuid3(uuid.NAMESPACE_DNS,settings.USER_INIT_DATABASE)
            prefix =  str(uuid3)[:8]
 
        # create uuidn
        uuidn =  prefix + "-" + str(uuid.uuid4())[9:]    

        user = self.model(
            username = username, 
            email = self.normalize_email(email),
            nid   = str(uuidn),
        )

        user.set_password(password)
        user.staff = is_staff
        user.admin = is_superuser

        if settings.SHARDING_USER_MODEL:
            user.save(using=str(db.get_name))
            db.count = db.count + 1
            db.save()
        else:
            user.save(using=self._db)
        return user

    def create_staffuser(self, username, email, password):
        """
        Creates and saves a staff user with the given email and password.
        """
        return self.create_user(username, email, password, is_staff = True)
    
    def create_superuser(self, username, email, password):
        """
        Creates and saves a superuser with the given email and password.
        """
        return self.create_user(username, email, password, is_staff = True, is_superuser= True) 

    def get_queryset(self):
        if self.model.SHAREDED_MODEL:
            if not self.model.db_for_write: # after, to change to db_for_read
                try:
                    db_list = Databases.objects.all().filter(model_name=self.model._meta.model_name).exclude(count=0)
                
                    if db_list.count() != 0:
                        #qs = MultiDBQuerySet(model=self.model, db_list=db_list)
                        #return reduce(QuerySetSequence, [super(ShardedModelManager, self).get_queryset().using(db.get_name) for db in db_list]) 
                        return reduce(QuerySetSequence, [ShardUserModelQueryset(self.model, using=db.get_name) for db in db_list]) 

                    return ShardUserModelQueryset(self.model, using=self._db).none()
                except:
                    return ShardUserModelQueryset(self.model, using=self._db)
            else:
                return ShardUserModelQueryset(self.model, using=self.model.db_for_write)
        else:
            return ShardUserModelQueryset(self.model, using=self._db)
    
    def raw_queryset(self, using = None):
        if using:
            return ShardUserModelQueryset(self.model, using=using)
        else:
            return ShardUserModelQueryset(self.model, using=self._db)


class ShardedUser(AbstractBaseUser):
    nid      = models.CharField(db_index=True, editable=False, max_length=36, unique=True, primary_key=True)
    username = models.CharField(verbose_name='Username', max_length=120,db_index=True, unique=True)
    email    = models.EmailField(verbose_name='email address', max_length=255, db_index=True, unique=True)
    active   = models.BooleanField(default=True)
    staff    = models.BooleanField(default=False) # a admin user; non super-user
    admin    = models.BooleanField(default=False) # a superuser
    date_joined = models.DateTimeField(editable=False, default=timezone.now)
    first_name  = models.CharField(verbose_name='First name', max_length=225)
    last_name   = models.CharField(verbose_name='First name', max_length=225)
    birth_date  = models.DateTimeField(default=timezone.now)
    # notice the absence of a "Password field", that is built in.

    objects = ShardedUserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ["username"] # Email & Password are required by default.

    if settings.SHARDING_USER_MODEL:
        SHAREDED_MODEL  = True
    else:
        SHAREDED_MODEL  = False
    
    class Meta:
        ordering = ['date_joined']
        abstract = True

    db_for_write    = None
    db_for_read     = None # not completed
    related_models  = [] # list of related data name
    forward_models  = []
    on_delete       = {}
    related_fields  = {}
    forward_fields  = {}
   
    def get_full_name(self):
        # The user is identified by their email address
        return self.first_name + ' ' + self.last_name

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __unicode__(self):  # on Python 2
        return self.email

    def __str__(self):             
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.staff

    @property
    def is_admin(self):
        "Is the user a admin member?"
        return self.admin

    @property
    def is_active(self):
        "Is the user active?"
        return self.active

    # for user multidatabase table save 
    def save(self, *args, **kwargs):

        if 'using' in kwargs:
            print("save user", 'saving using ' + kwargs['using'] + ' ...') 
        else:
            print("save user", 'saving ...')
 
        if settings.SHARDING_USER_MODEL:

            print("check if nid exist")
            print(self.nid)
            if self.nid:
                print("nid exist")
                # get prefix
                prefix = str(self.nid)[:8]
                # get database name
                db_name = Databases.objects.get_data_by_prefix(prefix)
                # save
                if "using" in kwargs:
                    print("save user", '2- saving kwargs using ' + kwargs['using'] + ' ...') 
                    super(AbstractBaseUser, self).save(*args, **kwargs)
                else:
                    print("save user", '2- saving db_name using ' + str(db_name) + ' ...') 
                    super(AbstractBaseUser, self).save(*args, **kwargs, using=str(db_name))

                # to delete after sharding permissions table
                # because permissions table are in default
                if self.is_admin and self.is_staff:
                    
                    kwargs['using'] ='default'
                    super(AbstractBaseUser, self).save(*args, **kwargs)
            else:
                print("nid not exist")
                # select database name
                db = select_write_db(model_name=self._meta.model_name)

                # get prefix
                prefix = db.get_prefix
                # create nid
                self.nid = str(prefix)+ "-" + str(uuid.uuid4())[9:]

                # write to selected database 
                print("save user", '2- saving using AbstractBaseUser') 

                super(AbstractBaseUser, self).save(*args, **kwargs)


                # to delete after sharding permissions table
                # because permissions table are in default
                if self.is_admin and self.is_staff:
                    kwargs['using'] ='default'
                    super(AbstractBaseUser, self).save(*args, **kwargs)#, using='default')
                                #except:
                                    #pass 

                # update count
                print("add count")
                db.count = db.count + 1
                db.save()

            if self.related_models is not None:
                for related_model in self.related_models:
                    # get related database
                    db_list = Databases.objects.all().filter(model_name=related_model._meta.model_name).exclude(count=0)  
                    # if exist
                    if db_list.count() != 0:
                        for db in db_list:
                            #try:
                            kwargs['using'] = str(db)
                            super(AbstractBaseUser, self).save(*args, **kwargs)
        else:
            super(AbstractBaseUser, self).save(*args, **kwargs)
        


################# Fields customizations ############################

class many_to_manyManager(models.Manager):
    use_for_related_fields = True
    def get_queryset(self):
        if self.model.using_db:
            qs = super(many_to_manyManager, self).get_queryset().using(self.model.using_db)
        else:
            qs = super(many_to_manyManager, self).get_queryset()
        return qs


################# All Models ############################

class ShardModelQueryset(models.QuerySet):

   #TODO: delete if related and forward on the same database
    def delete(self):
        print("deleting ...")
        count = self.count()
        for instance in self:

            print("get instance ...") #debug
            print(instance) #debug
            db = Databases.objects.get_data_by_full_name(instance._state.db)
            instance_db = instance._state.db
            self_pk  = instance.pk
            db.count = db.count - 1
            db.save()
        
            if instance.__class__.forward_models is not None:
                print("forward_fields", instance.__class__.forward_fields) # debug
                print("forward_models", instance.__class__.forward_models) # debug
                frd_pks = {}
                for forward_model in instance.__class__.forward_models:
                    attrname = instance.__class__.forward_fields[forward_model._meta.model_name]
                    frd_pks[getattr(instance, attrname + '_id')] = forward_model


            # 1- delete instance from its used database
            super(ShardModelQueryset,self).delete()

            # 2- same instance from related database:
            if instance.__class__.forward_models is not None:
                for frd_pk in frd_pks:
     
                    forward_model = frd_pks[frd_pk]
                    print(frd_pk, forward_model)

                    ct_model = ContentType.objects.get(model=forward_model._meta.model_name).model_class()
                    ct_model_obj = ct_model.objects.filter(pk= frd_pk)

                    print(ct_model_obj)

                    # do not delete forward_model instance if exist in his specific database
                    if ct_model_obj.count() == 0:
                        qs = models.QuerySet(forward_model, using=str(instance_db)).filter(pk= frd_pk)
                        print(qs)           
                        collector = Collector(using=instance_db)
                        collector.collect(qs)
                        deleted, _rows_count = collector.delete()

            # 3- delete related model instance from its database:
            # related_models: mean models where use this model in
            # this mean when delete this model instance will delete 
            # also in other model databases
            if instance.__class__.related_models is not None:
                print("get query set ...")
                print(instance.__class__.related_models)
                for related_model in instance.related_models:
                
                    print(instance.related_fields)    
                    db_list = Databases.objects.all().filter(model_name=related_model._meta.model_name).exclude(count=0)  
                    if db_list.count() != 0:
                        for db in db_list:
                            try: 
                                # on delete cascad
                                # if self.model.on_delete[related_model._meta.model_name].__name__ == "CASCADE":
                                #     filters = {}
                                #     # TODO: Change key dynamicly 
                                #     filters["owner"] = instance

                                #     qs1 = models.QuerySet(related_model, using=str(db)).filter(**filters)

                                #     collector = Collector(using=qs1.db)
                                #     collector.collect(qs1)
                                #     deleted, _rows_count = collector.delete()

                                filters = {}

                                filters[instance.related_fields[related_model._meta.model_name]] = instance

                                qs1 = models.QuerySet(related_model, using=str(db)).filter(**filters)

                                # on delete cascad delete related instances
                                if self.model.on_delete[related_model._meta.model_name].__name__ == "CASCADE":

                                    collector = Collector(using=qs1.db)
                                    collector.collect(qs1)
                                    deleted, _rows_count = collector.delete()

                                if qs1.count() == 0:
                                    # if related instance dosn't exist
                                    # delete this model instance in other model databases 
                                    print("self_pk ", self_pk)
                                    qs2 = models.QuerySet(self.model, using=str(qs1.db)).filter(pk= self_pk)
                                    print('qs2', qs2)           
                                    collector = Collector(using=qs1.db)
                                    collector.collect(qs2)
                                    deleted, _rows_count = collector.delete()


                            except instance.DoesNotExist:
                                continue

    def create(self,**kwargs):
  
        # use try/except to avoid re-create
        try:
            super(ShardModelQueryset,self).create(**kwargs)
        except IntegrityError:
            pass


class ShardedModelManager(models.Manager):

    def raw_queryset(self, using = None):
        if using:
            return ShardModelQueryset(self.model, using=using)
        else:
            return ShardModelQueryset(self.model, using=self._db)

    def get_queryset(self):
        if self.model.SHAREDED_MODEL:
            if not self.model.db_for_write: # after, to change to db_for_read
                try:
                    db_list = Databases.objects.all().filter(model_name=self.model._meta.model_name).exclude(count=0)
                
                    if db_list.count() != 0:
                        #qs = MultiDBQuerySet(model=self.model, db_list=db_list)
                        #return reduce(QuerySetSequence, [super(ShardedModelManager, self).get_queryset().using(db.get_name) for db in db_list]) 
                        return reduce(QuerySetSequence, [ShardModelQueryset(self.model, using=db.get_name) for db in db_list]) 

                    return ShardModelQueryset(self.model, using=self._db).none()
                except:
                    return ShardModelQueryset(self.model, using=self._db)
            else:
                return ShardModelQueryset(self.model, using=self.model.db_for_write)
        else:
            return ShardModelQueryset(self.model, using=self._db)

class ShardedModel(models.Model):

    nid   = models.CharField(db_index=True, editable=False, max_length=36, unique=True, primary_key=True)

    SHAREDED_MODEL  = True
    db_for_write    = None
    db_for_read     = None # not completed
    related_models  = [] # list of related model
    forward_models  = []
    on_delete       = {} # on delete action
    related_fields  = {}
    forward_fields  = {}

    objects = ShardedModelManager()

    class Meta:
        ordering = ['nid']
        abstract = True

    def save(self, *args, **kwargs):

        
        if 'using' in kwargs:
            print("save model", 'saving using ' + kwargs['using'] + ' ...')# for debug 
        else:
            print("save model", 'saving ...')# for debug

        if self.SHAREDED_MODEL:
            #print("in model save - self: ", self)# for debug

            #print("in model save - args: ", args)# for debug
            #print("in model save - kwargs: ", kwargs)# for debug

            if self.nid:
                #print("in model save - self.nid exist: ", self.nid)# for debug
                # get prefix
                prefix = str(self.nid)[:8]
                #print("in model save - prefix form nid: ", prefix)# for debug

                # get database name
                db_name = Databases.objects.get_data_by_prefix(prefix)
                #print("in model save - db_name form nid: ", db_name)# for debug

                # save
                if 'using' in kwargs:
                    super(ShardedModel, self).save(*args, **kwargs)
                else:
                    super(ShardedModel, self).save(*args, **kwargs, using=str(db_name))

            else:

                # select database name
                db = select_write_db(model_name=self._meta.model_name)
                #print("in model save - db: ", db) # for debug

                # get prefix
                prefix = db.get_prefix
                #print("in model save - prefix: ", prefix) # for debug

                # create nid
                self.nid = str(prefix)+ "-" + str(uuid.uuid4())[9:]
                #print("in model save - self.nid: ", self.nid) # for debug

                # write to selected database 
   
                super(ShardedModel, self).save(*args, **kwargs)

                # update count
                db.count = db.count + 1
                db.save()

            if self.related_models is not None:
                for related_model in self.related_models:
                    # get related database
                    db_list = Databases.objects.all().filter(model_name=related_model._meta.model_name).exclude(count=0)  
                    # if exist
                    if db_list.count() != 0:
                        for db in db_list:
                            #try:
                            kwargs['using'] = str(db)
                            super(ShardedModel, self).save(*args, **kwargs)
                
        else:
            super(ShardedModel, self).save(*args, **kwargs)


            