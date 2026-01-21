from django.urls import path
from .views import *

urlpatterns = [
    path('register/',register),
    path('login/',login),
    path('send-otp/',send_otp),
    path('verify-otp/',verify_otp),
    path('reset-password/',reset_password),
]