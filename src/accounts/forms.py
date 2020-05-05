from django import forms
from sharding.forms import ShardedUserRegisterForm, ShardedUserAdminCreationForm, ShardedUserAdminChangeForm, ShardedModelForm
from .models import User
from .models import Profile


class RegisterForm(ShardedUserRegisterForm):
    pass

class UserAdminCreationForm(ShardedUserAdminCreationForm):
    pass

class UserAdminChangeForm(ShardedUserAdminChangeForm):
    pass


class ProfileAdminCreationForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ( 'user', 'location', )

    # def save(self, commit=True):
    #     print("saving ... ")
    #     instance = super(ProfileAdminCreationForm, self).save(commit=False)

    #     return instance
