from django.shortcuts import render
from django.views import View
from django.http import HttpResponse

from sharding.models import Databases
from shop.models.products import Product

from sharding.multidbqueryset import MultiDBQuerySet

import uuid

from django.db.models.query import EmptyQuerySet, QuerySet

class HomePageView(View):

    def get(self, request, *args, **kwargs):

        ProductsA = Product.objects.filter(name="car1")
        ProductsB = Product.objects.filter(name="car1")
        

        print(ProductsA & ProductsB )
        

        context = {'Products': 'Products',
                   }
        
        content_type = ''#'application/xhtml+xml'
    
        Products1 = MultiDBQuerySet(model = Product).filter(name="car1")
        Products2 = MultiDBQuerySet(model = Product).filter(name="car1")


        print(Products1 & Products2 )

        return render(request, 'shop/index.html', context, content_type)



