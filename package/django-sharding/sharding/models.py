import uuid
from django.db import models

class DatabasesManager(models.Manager):

    def get_data_by_prefix(self, prefix):
        return self.get_queryset().filter(prefix=prefix).distinct().first()
    
    def get_data_by_full_name(self, full_name):
        full_name = full_name.split('_')
        model_name = full_name[0]
        number = full_name[1]
        return self.get_queryset().filter(model_name=model_name, number= number).distinct().first()

class Databases(models.Model):
    prefix     = models.CharField(max_length=8, db_index=True, unique=True, editable=False,)  
    model_name = models.CharField(max_length=20, db_index=True) # to be modified by content type name
    number     = models.IntegerField(db_index=True)
    count      = models.IntegerField()

    objects = DatabasesManager()

    def save(self, *args, **kwargs):
        database_name = self.model_name + "_ "+ str(self.number)
        uuid3 = uuid.uuid3(uuid.NAMESPACE_DNS,database_name)
        self.prefix = str(str(uuid3)[:8])
        super(Databases, self).save(*args, **kwargs)

    def __str__(self):
        return self.model_name + "_"+ str(self.number)

    @property
    def get_prefix(self):
        return self.prefix
    
    @property
    def get_name(self):
        return self.model_name + "_" + str(self.number)