from django.urls import path
from .views import (
    product_list, product_detail, register_view,
    login_view, logout_view, view_cart, add_to_cart, about
)

urlpatterns = [
    path('', product_list, name='product_list'),
    path('about/', about, name='about'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('cart/', view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),  # ← Важно!
]
