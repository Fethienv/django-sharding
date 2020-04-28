from django import forms
from sharding.forms import ShardedUserRegisterForm, ShardedUserAdminCreationForm, ShardedUserAdminChangeForm
from .models import User


class RegisterForm(ShardedUserRegisterForm):
    pass

class UserAdminCreationForm(ShardedUserAdminCreationForm):
    pass

class UserAdminChangeForm(ShardedUserAdminChangeForm):
    pass

