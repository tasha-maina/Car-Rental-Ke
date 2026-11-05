from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("book/<int:car_id>/", views.book, name="book"),
    path("pay/<str:ref>/", views.pay, name="pay"),
    path("pay/<str:ref>/status/", views.pay_status, name="pay_status"),
    path("pay/<str:ref>/stk/", views.stk, name="stk"),
    path("mpesa/callback/", views.mpesa_callback, name="mpesa_callback"),
    path("contact/", views.contact, name="contact"),
]
