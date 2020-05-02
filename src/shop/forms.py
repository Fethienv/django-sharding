
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from django.contrib.auth import get_user_model   
from django.core.exceptions import ValidationError 

from shop.models.products import Product
from .models.stores import Store
#from sharding.models import Databases

from sharding.forms import ShardedModelForm

User = get_user_model()

from itertools import islice, chain

class CustomMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.__str__()


class StoreAdminForm(forms.ModelForm):
    """A form for create and update Stores. """

    # def _save_m2m(self):
    #     """
    #     Save the many-to-many fields and generic relations for this form.
    #     """
    #     cleaned_data = self.cleaned_data
    #     exclude = self._meta.exclude
    #     fields = self._meta.fields
    #     opts = self.instance._meta
    #     # Note that for historical reasons we want to include also
    #     # private_fields here. (GenericRelation was previously a fake
    #     # m2m field).
    #     for f in chain(opts.many_to_many, opts.private_fields):
    #         if not hasattr(f, 'save_form_data'):
    #             continue
    #         if fields and f.name not in fields:
    #             continue
    #         if exclude and f.name in exclude:
    #             continue
    #         if f.name in cleaned_data:
    #             from django.core import serializers

                

    #             # data = serializers.serialize('json', cleaned_data['products2'])
    #             # print (data)
    #             # obj = serializers.deserialize('json', data, handle_forward_references=True)
    #             # print (obj.filter(pk='d45170fe-8895-4776-9d96-396573222905'))
    #             pass
    #             #f.save_form_data(self.instance, cleaned_data[f.name])

    # def save(self, commit=True):
    #     """
    #     Save this form's self.instance object if commit=True. Otherwise, add
    #     a save_m2m() method to the form which can be called after the instance
    #     is saved manually at a later time. Return the model instance.



    #     """
    #     #print(self.instance._meta.ShardedManyToManyField)

    #     #opts = self.instance._meta.ShardedManyToManyField

    #     #print("opts: ", opts)


    #     instance = super(StoreAdminForm, self).save(commit=False)

    #     return instance

    #p_products = CustomMultipleChoiceField(
     #   queryset=Product.objects.all()
    #)

    class Meta:
        model = Store
        fields = ( 'name', 'slug', 'products')#, "p_products") 

class ProductAdminChangeForm(forms.ModelForm):
    """A form for updating product. """

    class Meta:
        model = Product
        fields = ('name', 'slug', )

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
    