from django.urls import path
from . import views

urlpatterns = [
    path('products/',views.product_list,name='product_list'),
    path('products/<int:pk>/',views.product_detail,name='product_detail'),
    path('cart/',views.view_cart,name='view_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
     path('buy-now/', views.buy_now_checkout, name='buy_now_checkout'),
]

