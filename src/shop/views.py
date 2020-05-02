from django.shortcuts import render
from django.views import View
from django.http import HttpResponse

from sharding.models import Databases
from shop.models.products import Product
from shop.models.stores import Store, NormalStoreModel

from sharding.multidbquery import MultiDBQuerySet

import uuid

from django.db.models.query import EmptyQuerySet, QuerySet

class HomePageView(View):

    def get(self, request, *args, **kwargs):


        # Sharding tests
        ProductsA = Product.objects.filter(name="car")
        ProductsB = Product.objects.filter(name="car")

        print(ProductsA & ProductsB )
        

        context = {'Products': 'Products',
                   }
        
        content_type = ''#'application/xhtml+xml'
    
        # MultiDBQuerySet tests
        Products1 = MultiDBQuerySet(model = Product).filter(name="car")
        Products2 = MultiDBQuerySet(model = Product).filter(name="car")


        print(Products1 & Products2 )

        print("----------- NormalStore")
        store = NormalStoreModel.objects.first()

        

        print ("first: ", store.products.first())

        #print("product", NormalStoreModel.products)

        # for p in NormalStoreModel.products:
        #     print(p.nid)


        # manyToMany tests 
        print("----------- stores")
        stores = Store.objects.filter(name="jawlatte")#.using(s)
        #print("stores",stores.products) # limited need more work because it still return none

        print("----------- store")
        store = Store.objects.get(name="jawlatte") # get work well
        print("product test", store.products.all())


        

        return render(request, 'shop/index.html', context, content_type)



