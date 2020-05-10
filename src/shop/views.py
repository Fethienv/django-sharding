from django.shortcuts import render
from django.views import View
from django.http import HttpResponse

from sharding.models import Databases
from shop.models.products import Product
from shop.models.stores import Store, NormalStoreModel

from sharding.multidbquery import MultiDBQuerySet

import uuid

from django.db.models.query import EmptyQuerySet, QuerySet

from django.contrib import auth

User = auth.get_user_model()

class HomePageView(View):

    def get(self, request, *args, **kwargs):


        # Sharding tests
        # ProductsA = Product.objects.filter(name="car")
        # ProductsB = Product.objects.filter(name="car")

        # print(ProductsA & ProductsB )
        

        context = {'Products': 'Products',
                   }
        
        content_type = ''#'application/xhtml+xml'
    
        # MultiDBQuerySet tests
        # Products1 = MultiDBQuerySet(model = Product).filter(name="car")
        # Products2 = MultiDBQuerySet(model = Product).filter(name="car")


        # print(Products1 & Products2 )


        # ForeingKey tests 

        Products = Product.objects.all()
        for pp in Products:
            print(pp.vendor)

        # # manyToMany tests 
        # print("----------- manyToMany tests ")
        # stores = Store.objects.filter(name="jawlatte")#.using(s)
        # #print("stores",stores.products) # limited need more work because it still return none

        # store = Store.objects.get(name="jawlatte") # get work well
        # print("product test", store.products.all())


        # OneToOne tests 
        # print("----------- OneToOne tests")
        # user = User.objects.get(email="testing@test.com")
        # print("user", user.nid)
        # print("user profile: ", user.profile)

        # problems
        # 1. to set profile must user exist in profile db
        # 2. to get profile must profile exist in default
        # To do during set must read user from user table, and during get must read profile from profile table
        # 
        

        return render(request, 'shop/index.html', context, content_type)



