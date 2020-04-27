
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from shop.models.products import Product

class ProductAdminChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    #password = ReadOnlyPasswordHashField()

    #name  = models.CharField(db_index=True, max_length=120)
    #slug  = models.SlugField(db_index=True, unique=True )
   

    class Meta:
        model = Product
        fields = ('name', 'slug', )


    # def save(self, commit=True):

    #     vendor = self.cleaned_data.get("vendor")
    #     print(vendor)

    #     mm = self.model()
    #     print(mm)

    #     product = super(UserAdminCreationForm, self).save(commit=False, vendor="123456")
    #     # Save the provided password in hashed format

    #     # uuid3 = uuid.uuid3(uuid.NAMESPACE_DNS,'sahari')
    #     # uuid4 = uuid.uuid4()
    #     # uuidn =  str(uuid3)[:9] + str(uuid4)[9:]  
    #     # 
         
        
    #     product = super(ProductAdminChangeForm, self).save(commit=False)
    #     #print(product) 
    #     #.slug
    #     # user.nid   = str(uuidn)
    #     # user.set_password(self.cleaned_data["password1"])
    #     # if commit:
    #     #     user.save()
    #     return product

from django.contrib.auth import get_user_model   
from django.core.exceptions import ValidationError 
User = get_user_model()

#from sharding.models import Databases

class ProductAdminCreationForm(forms.ModelForm):
    """
    A form for creating new Prodct. 
    """

    class Meta:
        model = Product
        fields = ( 'name', 'slug', 'vendor')
        #readonly_fields = ["nid",]

    def clean_vendor(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value

        # search vendor by database
        vendor_instance = self.cleaned_data.get("vendor")
        #prefix    = str(vendor_instance.nid)[:8]
        #db = Databases.objects.get_data_by_prefix(prefix)
        #vendor    = User.objects.filter(nid=vendor_instance.nid).using(db.get_name)

        #if vendor.count() == 0:
            #raise ValidationError("Vendor dosn't exist")

        #vendor_instance = vendor.first()
        
        return vendor_instance

    # def clean(self):
    #     pass
    #     #cleaned_data = super().clean()
    #     # cc_myself = cleaned_data.get("cc_myself")
    #     # subject = cleaned_data.get("subject")

    #     # if cc_myself and subject:
    #     #     # Only do something if both fields are valid so far.
    #     #     if "help" not in subject:
    #     #         raise forms.ValidationError(
    #     #             "Did not send for 'help' in the subject despite "
    #     #             "CC'ing yourself."
    #     #         )

    # def clean(self):
    #     #super().clean()

    #     print("Instance", self.instance)

    #     # #for form in self.forms:
    #     #     name = form.cleaned_data['name'].upper()
    #     #     form.cleaned_data['name'] = name
    #     #     # update the instance value.
    #     #     form.instance.name = name

    #     vendor_instance = self.cleaned_data.get("vendor")

    #     vendor    = User.objects.filter(nid=vendor_instance.nid).first()
    #     print (vendor)
        

    #     self.instance.vendor = vendor
    #     return self.instance

    # def save(self, commit=True):
    #     # Save the provided password in hashed format

    #     print(self.cleaned_data)
    #     product = super(ProductAdminCreationForm, self).save(commit=False)

        # uuid3 = uuid.uuid3(uuid.NAMESPACE_DNS,'sahari')
        # uuid4 = uuid.uuid4()
        # uuidn =  str(uuid3)[:9] + str(uuid4)[9:]    

        # user = super(UserAdminCreationForm, self).save(commit=False)
        # user.nid   = str(uuidn)
        # user.set_password(self.cleaned_data["password1"])
        # if commit:
        #     user.save()
        #return product
    