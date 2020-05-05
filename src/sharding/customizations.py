
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


class ShardUserModelQueryset(models.QuerySet):

    def delete(self):
        print("deleting ...")
        count = self.count()
        if self.model.related_models is not None and count == 1:
            print("get instance ...")
            instance = self.first()
        #cascade_delete(User)
        super(ShardUserModelQueryset,self).delete()

        if self.model.related_models is not None and count == 1:
            print("get query set ...")
            for related_model in self.model.related_models:

                db_list = Databases.objects.all().filter(model_name=related_model._meta.model_name).exclude(count=0)  
                if db_list.count() != 0:
                    for db in db_list:
                        try: 
                            # on delete cascad
                            if self.model.on_delete[related_model._meta.model_name].__name__ == "CASCADE":
                                # 1- delete related:
                                qs1 = related_model.objects.get(user=instance) #models.QuerySet(related_model, using=str(db)).filter(pk= str(instance.pk))
                                qs1.delete()

                                # 2- delete the same instance from related database 
                                  
                                qs = models.QuerySet(self.model, using=str(db)).filter(pk= instance.pk)

                                collector = Collector(using=qs.db)
                                collector.collect(qs)
                                deleted, _rows_count = collector.delete()

                        except self.model.DoesNotExist:
                            continue

 
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
            #try:
                # to delete after sharding permissions table
                # because permissions table are in default
            if is_staff and is_superuser:
                #kwargs['using'] ='default'
                user.save(using='default')

            user.save(using=str(db.get_name))
            #except:
                #raise Error(f"No database for {self.model._meta.model_name} Model, please add it from admin")
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

    # def get_queryset(self):
    #     if settings.SHARDING_USER_MODEL:
    #         if not self.model.db_for_write: # after, to change to db_for_read
    #             try:
    #                 db_list = Databases.objects.all().filter(model_name=self.model._meta.model_name).exclude(count=0)
                
    #                 if db_list.count() != 0:
    #                     #return MultiDBQuerySet(model=self.model, db_list=db_list)
    #                     return reduce(QuerySetSequence, [super(ShardedUserManager, self).get_queryset().using(db.get_name) for db in db_list])        
    #                 return super(ShardedUserManager, self).get_queryset().none()
    #             except:
    #                 return super(ShardedUserManager, self).get_queryset() 
    #         else:
    #             return super(ShardedUserManager, self).get_queryset().using(self.model.db_for_write)
    #     else:
    #         return super(ShardedUserManager, self).get_queryset()

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

    # def delete(self):
    #     print("related_dbs")
    #     return self.get_queryset().delete()


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

    db_for_write    = None
    db_for_read     = None # not completed
    related_models  = [] # list of related data name
    forward_models  = []
    on_delete       = {}

    # def delete(self, using=None,keep_parents=False):
    #     print("testing")
    #     super(ShardedUser, self).delete(using=using, keep_parents=keep_parents)
   
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
            
            if self.nid:
                # get prefix
                prefix = str(self.nid)[:8]
                # get database name
                db_name = Databases.objects.get_data_by_prefix(prefix)
                # save
                if "using" in kwargs:
                    super(AbstractBaseUser, self).save(*args, **kwargs)
                else:
                    super(AbstractBaseUser, self).save(*args, **kwargs, using=str(db_name))

                # to delete after sharding permissions table
                # because permissions table are in default
                if self.is_admin and self.is_staff:
                    kwargs['using'] ='default'
                    super(AbstractBaseUser, self).save(*args, **kwargs)
            else:
                # select database name
                db = select_write_db(model_name=self._meta.model_name)

                # get prefix
                prefix = db.get_prefix
                # create nid
                self.nid = str(prefix)+ "-" + str(uuid.uuid4())[9:]

                # write to selected database 
                #if 'using' in kwargs:
                super(AbstractBaseUser, self).save(*args, **kwargs)
                #else:
                    #super(ShardedUser, self).save(*args, **kwargs, using=str(db.get_name))

                # to delete after sharding permissions table
                # because permissions table are in default
                if self.is_admin and self.is_staff:
                    kwargs['using'] ='default'
                    super(AbstractBaseUser, self).save(*args, **kwargs)#, using='default')

                # update count
                print("add count")
                db.count = db.count + 1
                db.save()
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
    def delete(self):
        print("deleting ...")
        count = self.count()
        if count == 1:
            print("get instance ...")
            instance = self.first()
        #cascade_delete(User)
        if self.model.forward_models is not None and count == 1:
            frd_pks = {}
            for forward_model in self.model.forward_models:
                frd_pks[getattr(self.first(), forward_model._meta.model_name + '_id')] = forward_model

        super(ShardModelQueryset,self).delete()

        if self.model.forward_models is not None and count == 1:
            for frd_pk in frd_pks:
     
                forward_model = frd_pks[frd_pk]
                print(frd_pk, forward_model)
                qs = models.QuerySet(forward_model, using=str(self.db)).filter(pk= frd_pk)
                print(qs)

                collector = Collector(using=self.db)
                collector.collect(qs)
                deleted, _rows_count = collector.delete()


        if self.model.related_models is not None and count == 1:
            print("get query set ...")
            for related_model in self.model.related_models:

                db_list = Databases.objects.all().filter(model_name=related_model._meta.model_name).exclude(count=0)  
                if db_list.count() != 0:
                    for db in db_list:
                        try: 
                            # on delete cascad
                            if self.model.on_delete[related_model._meta.model_name].__name__ == "CASCADE":
                                # 1- delete related:
                                qs1 = related_model.objects.get(user=instance) #models.QuerySet(related_model, using=str(db)).filter(pk= str(instance.pk))
                                qs1.delete()

                                # 2- delete the same instance from related database 
                                  
                                qs = models.QuerySet(self.model, using=str(db)).filter(pk= instance.pk)

                                collector = Collector(using=qs.db)
                                collector.collect(qs)
                                deleted, _rows_count = collector.delete()

                        except self.model.DoesNotExist:
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

    # def get_queryset(self):
    #     if self.model.SHAREDED_MODEL:
    #         if not self.model.db_for_write: # after, to change to db_for_read
    #             try:
    #                 db_list = Databases.objects.all().filter(model_name=self.model._meta.model_name).exclude(count=0)
                
    #                 if db_list.count() != 0:
    #                     #qs = MultiDBQuerySet(model=self.model, db_list=db_list)
    #                     return reduce(QuerySetSequence, [super(ShardedModelManager, self).get_queryset().using(db.get_name) for db in db_list]) 

    #                 return super(ShardedModelManager, self).get_queryset().none()
    #             except:
    #                 return super(ShardedModelManager, self).get_queryset() 
    #         else:
    #             return super(ShardedModelManager, self).get_queryset().using(self.model.db_for_write)
    #     else:
    #         return super(ShardedModelManager, self).get_queryset()

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

    objects = ShardedModelManager()

    class Meta:
        ordering = ['nid']
        abstract = True


    # def delete(self, using=None,keep_parents=False):
    #     super(ShardedModel, self).save(*args, **kwargs, using=using)
    

    def save(self, *args, **kwargs):

        
        if 'using' in kwargs:
            print("save model", 'saving using ' + kwargs['using'] + ' ...') 
        else:
            print("save model", 'saving ...')

        if self.SHAREDED_MODEL:
            #print("in model save - self: ", self)

            #print("in model save - args: ", args)
            #print("in model save - kwargs: ", kwargs)

            
            if self.nid:
                #print("in model save - self.nid exist: ", self.nid)
                # get prefix
                prefix = str(self.nid)[:8]
                #print("in model save - prefix form nid: ", prefix)
                # get database name
                db_name = Databases.objects.get_data_by_prefix(prefix)
                #print("in model save - db_name form nid: ", db_name)
                # save
                #Product
                #if not self.db_for_write:
                if 'using' in kwargs:
                    super(ShardedModel, self).save(*args, **kwargs)
                else:
                    super(ShardedModel, self).save(*args, **kwargs, using=str(db_name))
                #else:
                    #if 'using' in kwargs:
                    #kwargs["using"] = self.db_for_write
                    #super(ShardedModel, self).save(*args, **kwargs)
                    #else:
                        #super(ShardedModel, self).save(*args, **kwargs, using=str(self.db_for_write))
            else:
                # select database name
                db = select_write_db(model_name=self._meta.model_name)
                #print("in model save - db: ", db)

                # get prefix
                prefix = db.get_prefix
                #print("in model save - prefix: ", prefix)

                # create nid
                self.nid = str(prefix)+ "-" + str(uuid.uuid4())[9:]
                #print("in model save - self.nid: ", self.nid)

                # write to selected database 
                #if not self.db_for_write:
                    #if 'using' in kwargs:
                super(ShardedModel, self).save(*args, **kwargs)
                    #else:
                        #super(ShardedModel, self).save(*args, **kwargs, using=str(db.get_name))
                    # update count
                db.count = db.count + 1
                db.save()
                #else:
                    #if 'using' in kwargs:
                        #super(ShardedModel, self).save(*args, **kwargs)
                    #else:
                        #super(ShardedModel, self).save(*args, **kwargs, using=str(self.db_for_write))
                
        else:
            #if not self.db_for_write:
                #super(ShardedModel, self).save(*args, **kwargs) 
            #else:
               # if 'using' in kwargs:
            super(ShardedModel, self).save(*args, **kwargs)
                #else:
                    #super(ShardedModel, self).save(*args, **kwargs, using=str(self.db_for_write))

            

    # save m2m solutions

    #def delete(self, *args, **kwargs):

