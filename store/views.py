from django.shortcuts import render
from .models import Product




def product_list(request):
    products = Product.objects.all() # берём все товары
    return render(request, 'store/product_list.html', {
    'products': products
    })