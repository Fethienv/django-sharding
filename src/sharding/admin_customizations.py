
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import ShardedUserRegisterForm, ShardedUserAdminCreationForm, ShardedUserAdminChangeForm

################# User Admin Model ############################
class ShardedUserAdminModel(BaseUserAdmin):
    # The forms to add and change user instances
    form = ShardedUserAdminChangeForm 
    add_form = ShardedUserAdminCreationForm

    readonly_fields=('last_login',"date_joined")

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'admin')
    list_filter = ('admin',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name','last_name','birth_date',)}),
        ('Login info', {'fields': ("last_login", "date_joined",)}),
        ('Permissions', {'fields': ('admin','staff')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()