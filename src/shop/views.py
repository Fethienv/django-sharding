from django.shortcuts import render
from django.views import View
from django.http import HttpResponse

from sharding.models import Databases
from shop.models.products import Product

import uuid

# from .models.products import Product

class HomePageView(View):

    def get(self, request, *args, **kwargs):

        Products = Product.objects.all()

        print(Products)

        context = {'Products': 'Products',
                   }
        
        content_type = ''#'application/xhtml+xml'

        for a in Products:
            print(a)

        return render(request, 'shop/index.html', context, content_type)



