from django.contrib import admin
from django.contrib.admin import AdminSite
from django.conf import settings
from django.http import HttpResponse

from .models.products import Product
from django.conf.urls import url

from .forms import ProductAdminChangeForm, ProductAdminCreationForm
from sharding.models import Databases

class MyAdminSite(AdminSite):

    def custom_view(self, request):
        return HttpResponse("Test")

    def get_urls(self):
        
        urls = super(MyAdminSite, self).get_urls()
        urls += [
            url(r'^custom_view/$', self.admin_view(self.custom_view))
        ]
        return urls

admin_site = MyAdminSite()



#@admin.register(Product)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ['name',]
    search_fields = ('name',)
    list_per_page = 15
    #view_on_site = True
    #list_select_related = True
    #readonly_fields=('nid',)
    change = ProductAdminChangeForm
    form   = ProductAdminCreationForm

    # def get_form(self, request, obj=None, **kwargs):
    #     self.nid = obj.nid
    #     self.obj = obj
    #     return super(ProductsAdmin, self).get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):

        try: 
            if self.nid:
                prefix = str(self.nid)[:8]
                db_name = Databases.objects.get_data_by_prefix(prefix)
                db_name = Databases.objects.get_data_by_prefix(prefix)
                product = Product.objects.raw_queryset(str(db_name)).get(nid=self.nid)

                print("product:", product)

                product.name = form.cleaned_data.get("name")
                product.slug = form.cleaned_data.get("slug")
                product.vendor = form.cleaned_data.get("vendor")
            
                product.save()

                return super(ProductsAdmin, self).save_model(request, product, form, change)
        except:
            return super(ProductsAdmin, self).save_model(request, obj, form, change)


    # def queryset (self, request):
    #     qs = Product.objects.all()
    #     ordering = self.get_ordering(request)
    #     if ordering:
    #         qs = qs.order_by(*ordering)
    #     return qs
    
    # def get_queryset(self, request):



    #     qs = super(ProductsAdmin, self).get_queryset(request)       

    #     ordering = self.get_ordering(request)
    #     if ordering:
    #         qs = qs.order_by(*ordering)

    #     #if request.user.is_superuser:
    #         #return qs
    #     return qs#.filter(author=request.user)




admin.site.register(Product, ProductsAdmin)











#     # A handy constant for the name of the alternate database.
#     using = 'shop-primary'

#     def save_model(self, request, obj, form, change):
#         # Tell Django to save objects to the 'other' database.
#         obj.save(using=self.using)

#     def delete_model(self, request, obj):
#         # Tell Django to delete objects from the 'other' database
#         obj.delete(using=self.using)

#     def get_queryset(self, request):
#         # Tell Django to look for objects on the 'other' database.
#         import random
#         from itertools import chain
#         db_list = settings.HORIZONTAL_CONFIG['GROUPS'][Product._meta.horizontal_group]['DATABASES']

#         qs = {}

#         for data in db_list:
#             db = random.choice(db_list[data]['read'])
#             qs[data] = super().get_queryset(request).using(db)

#             # get all from all 
        
         
#         q = qs[2] | qs[3] 
#         print(q)     
#         return q#super().get_queryset(request).using(self.using)

#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         # Tell Django to populate ForeignKey widgets using a query
#         # on the 'other' database.
#         return super().formfield_for_foreignkey(db_field, request, using=self.using, **kwargs)

#     def formfield_for_manytomany(self, db_field, request, **kwargs):
#         # Tell Django to populate ManyToMany widgets using a query
#         # on the 'other' database.
#         return super().formfield_for_manytomany(db_field, request, using=self.using, **kwargs)


