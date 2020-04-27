from django import forms
from sharding.forms import ShardedRegisterForm, ShardedUserAdminCreationForm, ShardedAdminChangeForm
from .models import User


class RegisterForm(ShardedRegisterForm):
    pass

class UserAdminCreationForm(ShardedUserAdminCreationForm):
    pass

class UserAdminChangeForm(ShardedAdminChangeForm):
    pass

