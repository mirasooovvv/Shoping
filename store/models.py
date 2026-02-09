from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse




class Product(models.Model):
    name = models.CharField(max_length=100) # название
    price = models.CharField(max_length=100) # цена
    description = models.TextField(blank=True) # описание (необязательно)


    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'product_id': self.id})
    
class Order(models.Model):
    Product = models.ForeignKey(Product, on_delete=models.CASCADE)
    payment_id = models.CharField (max_length=250)
    status = models.CharField(max_length=50, default='pending')
    
    
    
