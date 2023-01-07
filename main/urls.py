from django.contrib import admin
from django.urls import path,include
from . import views


urlpatterns = [
    path("" , views.index, name = "index"),
    path("product", views.product, name="product"),
    path("video",views.video, name="video"),
    path("data",views.data, name="data"),
    path("contact-us",views.contact, name="contact-us"),
]
