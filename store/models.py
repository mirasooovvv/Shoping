from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Product(models.Model):
    name = models.CharField(max_length=100)  # название товара
    price = models.DecimalField(max_digits=10, decimal_places=2)  # цена товара, используем DecimalField
    description = models.TextField(blank=True)  # описание товара

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'product_id': self.id})


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # связь с пользователем
    created_at = models.DateTimeField(auto_now_add=True)  # дата создания корзины

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)  # связь с корзиной
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # связь с товаром
    quantity = models.PositiveIntegerField(default=1)  # количество товара в корзине

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        """Возвращает общую стоимость для данного товара в корзине."""
        return self.product.price * self.quantity  # используем Decimal для точных вычислений


class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # связь с продуктом
    payment_id = models.CharField(max_length=250)  # ID платежа
    status = models.CharField(max_length=50, default='pending')  # статус заказа
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  # связь с пользователем (если нужно)

    def __str__(self):
        return f"Order {self.id} for {self.product.name} by {self.user.username if self.user else 'Guest'}"
