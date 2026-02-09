from django.urls import path
from .views import (
    product_list, product_detail, register_view,
<<<<<<< HEAD
    login_view, logout_view, view_cart, add_to_cart, about, cart_sidebar,
    create_payment, payment_success, create_payment_cart
=======
    login_view, logout_view, view_cart, add_to_cart, about, remove_from_cart,
    update_cart_item
>>>>>>> 3e8f6cde7d8fabcbdaea845680eb15ab5cba5f58
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
<<<<<<< HEAD
    path('cart/sidebar/', cart_sidebar, name='cart_sidebar'),
    path('pay/<int:product_id>/', create_payment, name='create_payment'),
    path('pay/cart/', create_payment_cart, name='create_payment_cart'),
    path('payment-success/', payment_success, name='payment_success')
=======
    path('cart/remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),  # ← Важно!
    path('cart/update/<int:product_id>/', update_cart_item, name='update_cart_item'),  # ← Важно!
>>>>>>> 3e8f6cde7d8fabcbdaea845680eb15ab5cba5f58
]

