from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import Product, Order, CartItem, Cart
from yookassa import Configuration, Payment
from django.conf import settings
import uuid

# Настройка YoKassa (глобальная)
Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

# ---------- PAYMENT ----------


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from yookassa import Payment
from .models import Product, Order, Cart
from django.conf import settings
import uuid

# Конфигурация YoKassa API
from yookassa import Configuration
Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

# Функция для создания платежа для отдельного продукта
def create_payment(request, product_id):
    # Получаем продукт из базы данных
    product = get_object_or_404(Product, id=product_id)
    idempotence_key = str(uuid.uuid4())  # Генерация уникального idempotence_key

    try:
        # Создаем данные для платежа
        payment_data = {
            "amount": {
                "value": str(product.price),  # Цена продукта
                "currency": "RUB"  # Убедитесь, что валюта правильная
            },
            "confirmation": {
                "type": "redirect",  # Способ подтверждения
                "return_url": request.build_absolute_uri('/payment-success/')  # URL возврата
            },
            "capture": True,  # Убедитесь, что захват средств разрешен
            "description": f"Оплата {product.name}"  # Описание платежа
        }

        # Создаем платеж, передавая только два аргумента
        payment = Payment.create(payment_data, idempotence_key)

        # Создаем заказ с состоянием "pending"
        Order.objects.create(
            product=product,
            payment_id=payment.id,
            status="pending"
        )

        # Перенаправляем пользователя на страницу подтверждения платежа (ЮKassa)
        return redirect(payment.confirmation.confirmation_url)

    except Exception as e:
        # Обработка ошибок
        print(f"--- ОШИБКА ЮKASSA: {e} ---")
        messages.error(request, f"Ошибка платежной системы: {e}")
        return redirect('product_detail', product_id=product.id)
    
# Функция для создания платежа по корзине товаров
def create_payment_cart(request):
    items_to_save = []
    total = 0

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        for item in cart.items.all():
            items_to_save.append(item.product)
            total += item.get_total_price()
    else:
        session_cart = request.session.get('cart', {})
        for pid, qty in session_cart.items():
            product = Product.objects.filter(id=pid).first()
            if product:
                items_to_save.append(product)
                total += product.price * qty

    if total == 0:
        messages.warning(request, "Ваша корзина пуста.")
        return redirect('view_cart')

    try:
        # Создание платежа с правильными данными
        payment_data = {
            "amount": { 
                "value": str(total),  # Общая сумма
                "currency": "RUB"  # Убедитесь, что используете правильную валюту
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "http://127.0.0.1:8000/payment-success/"
            },
            "capture": True,
            "description": "Оплата корзины"
        }

        # Создаем платеж, передавая только два аргумента
        payment = Payment.create(payment_data, str(uuid.uuid4()))

        # Создание заказов для каждого продукта в корзине
        for product in items_to_save:
            Order.objects.create(product=product, payment_id=payment.id, status='pending')

        # Перенаправляем пользователя на страницу подтверждения платежа
        return redirect(payment.confirmation.confirmation_url)

    except Exception as e:
        # Если произошла ошибка, показываем сообщение об ошибке
        messages.error(request, f"Ошибка оплаты корзины: {e}")
        return redirect('view_cart')


# Функция для успешной оплаты
def payment_success(request):
    return render(request, "payment_success.html")

# ---------- AUTH ----------

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Вы успешно зарегистрированы!")
            return redirect("product_list")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Вы успешно вошли!")
            return redirect("product_list")
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.success(request, "Вы успешно вышли!")
    return redirect("login")

# ---------- STORE ----------

def product_list(request):
    products = Product.objects.all()
    return render(request, "store/product_list.html", {"products": products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "store/product_detail.html", {"product": product})

def about(request):
    return render(request, "store/about.html")

# ---------- CART ----------

def view_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        items = cart.items.all()
        total_price = sum(item.get_total_price() for item in items)
    else:
        session_cart = request.session.get('cart', {})
        items = []
        total_price = 0
        for pid, qty in session_cart.items():
            try:
                product = Product.objects.get(id=pid)
                total = product.price * qty
                items.append({'product': product, 'quantity': qty, 'total_price': total})
                total_price += total
            except Product.DoesNotExist:
                continue
    
    return render(request, "cart/cart.html", {
        "items": items, 
        "total_price": total_price
    })

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": 1})
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    else:
        cart = request.session.get('cart', {})
        key = str(product.id)
        cart[key] = cart.get(key, 0) + 1
        request.session['cart'] = cart
    return redirect("view_cart")

@login_required
def remove_from_cart(request, product_id):
    cart = Cart.objects.get(user=request.user)
    CartItem.objects.filter(cart=cart, product_id=product_id).delete()
    return redirect('view_cart')

@login_required
def update_cart_item(request, product_id):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    action = request.GET.get('action')
    if action == "inc":
        item.quantity += 1
        item.save()
    elif action == "dec":
        item.quantity -= 1
        if item.quantity <= 0:
            item.delete()
        else:
            item.save()
    return redirect('view_cart')

def cart_sidebar(request):
    items = []
    total_price = 0
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.all()
        total_price = sum(i.get_total_price() for i in items)
    return render(request, 'cart/_cart_sidebar.html', {'items': items, 'total_price': total_price})