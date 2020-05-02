from django.shortcuts import render
from django.views import View
from django.http import HttpResponse

from sharding.models import Databases
from shop.models.products import Product
from shop.models.stores import Store

from sharding.multidbquery import MultiDBQuerySet

import uuid

from django.db.models.query import EmptyQuerySet, QuerySet

class HomePageView(View):

    def get(self, request, *args, **kwargs):


        # Sharding tests
        #ProductsA = Product.objects.filter(name="car")
        #ProductsB = Product.objects.filter(name="car")

        #print(ProductsA & ProductsB )
        

        context = {'Products': 'Products',
                   }
        
        content_type = ''#'application/xhtml+xml'
    
        # MultiDBQuerySet tests
        #Products1 = MultiDBQuerySet(model = Product).filter(name="car")
        #Products2 = MultiDBQuerySet(model = Product).filter(name="car")


        #print(Products1 & Products2 )


        # manyToMany tests 
        stores = Store.objects.filter(name="jawlatte.com")
        print("stores",stores.first().products) # limited need more work because it still return none
        
        store = Store.objects.get(name="jawlatte.com") # get work well
        print("product", store.products)
        

        return render(request, 'shop/index.html', context, content_type)



