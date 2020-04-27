from django.contrib import admin
from django.urls import path

from .views import  HomePageView


app_name = "shop"

urlpatterns = [
    path('',  HomePageView.as_view(), name="index"),
]
