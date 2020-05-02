from django.contrib import admin
from django.contrib.admin import AdminSite
from django.conf import settings
from django.http import HttpResponse

from .models.products import Product, NormalProductModel
from .models.stores import Store, NormalStoreModel
from django.conf.urls import url

from .forms import ProductAdminCreationForm, StoreAdminForm
from sharding.models import Databases

@admin.register(Store)
class StoresAdmin(admin.ModelAdmin):
    form   = StoreAdminForm

@admin.register(NormalStoreModel)
class NormalStoreAdmin(admin.ModelAdmin):
    pass

@admin.register(NormalProductModel)
class NormalProductAdmin(admin.ModelAdmin):
    pass

@admin.register(Product)
class ProductsAdmin(admin.ModelAdmin):
    #list_display = ['name',]
    #search_fields = ('name',)
    #list_per_page = 15
    #view_on_site = True
    #list_select_related = True
    #readonly_fields=('nid',)
    #change = ProductAdminChangeForm
    form   = ProductAdminCreationForm

    # def get_form(self, request, obj=None, **kwargs):
    #     self.nid = obj.nid
    #     self.obj = obj
    #     return super(ProductsAdmin, self).get_form(request, obj, **kwargs)

    # def save_model(self, request, obj, form, change):

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




#     def save_model(self, request, obj, form, change):
#         # Tell Django to save objects to the 'other' database.
#         obj.save(using=self.using)

#     def delete_model(self, request, obj):
#         # Tell Django to delete objects from the 'other' database
#         obj.delete(using=self.using)

#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         # Tell Django to populate ForeignKey widgets using a query
#         # on the 'other' database.
#         return super().formfield_for_foreignkey(db_field, request, using=self.using, **kwargs)

#     def formfield_for_manytomany(self, db_field, request, **kwargs):
#         # Tell Django to populate ManyToMany widgets using a query
#         # on the 'other' database.
#         return super().formfield_for_manytomany(db_field, request, using=self.using, **kwargs)


