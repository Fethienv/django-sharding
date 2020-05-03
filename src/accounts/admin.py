from django.contrib import admin, auth

from django.contrib.auth.models import Group
from sharding.admin_customizations import ShardedUserAdminModel
from .models import Profile
from .forms import ProfileAdminCreationForm

User = auth.get_user_model()

class UserAdmin(ShardedUserAdminModel):
    pass

admin.site.register(User, UserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form   = ProfileAdminCreationForm
    # def save_model(self, request, obj, form, change):
    #     return super(ProfileAdmin, self).save_model(request, obj, form, change)

    #     try: 
    #         if self.nid:
    #             prefix = str(self.nid)[:8]
    #             db_name = Databases.objects.get_data_by_prefix(prefix)
    #             db_name = Databases.objects.get_data_by_prefix(prefix)
    #             product = Product.objects.raw_queryset(str(db_name)).get(nid=self.nid)

    #             print("product:", product)

    #             product.name = form.cleaned_data.get("name")
    #             product.slug = form.cleaned_data.get("slug")
    #             product.vendor = form.cleaned_data.get("vendor")
            
    #             product.save()

    #             return super(ProductsAdmin, self).save_model(request, product, form, change)
    #     except:
    #         return super(ProductsAdmin, self).save_model(request, obj, form, change)

# Remove Group Model from admin. We're not using it.
admin.site.unregister(Group)
