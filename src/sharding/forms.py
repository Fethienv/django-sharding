import uuid
from django import forms
from django.db import Error
from django.conf import settings
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from django.contrib.auth import get_user_model
from .models import Databases
from .utils import select_write_db

User = get_user_model()

class ShardedModelForm(forms.ModelForm):

    def save(self, commit=True):
        
        db = select_write_db(model_name=self._meta.model._meta.model_name)

        # get prefix
        if not db:
            uuid3  = uuid.uuid3(uuid.NAMESPACE_DNS,'default')
            prefix =  str(uuid3)[:8]
        else:    
            prefix = db.get_prefix 

        Instance = super(ShardedModelForm, self).save(commit=False)

        Instance.nid   = prefix + "-" + str(uuid.uuid4())[9:] 

        if commit:
            Instance.save(commit=False)
        return Instance

class ShardedUserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if qs.exists():
            raise forms.ValidationError("email is taken")
        return email

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

class ShardedUserAdminCreationForm(ShardedModelForm):
    """
    A form for creating new users. Includes all the required
    fields, plus a repeated password.
    """
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        
        # db = select_write_db(model_name=self._meta.model._meta.model_name)

        # # get prefix
        # if not db:
        #     uuid3  = uuid.uuid3(uuid.NAMESPACE_DNS,'default')
        #     prefix =  str(uuid3)[:8]
        # else:    
        #     prefix = db.get_prefix 

        user = super(ShardedUserAdminCreationForm, self).save(commit=False)

        #user.nid   = prefix + "-" + str(uuid.uuid4())[9:] 

        # Save the provided password in hashed format
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save(commit=False)
        return user


class ShardedUserAdminChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()
    
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name','last_name','birth_date', 'active', 'admin', 'staff')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]

