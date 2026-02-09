from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from .forms import RegisterForm, LoginForm
from .models import Product, Order
from .Cart import Cart, CartItem
from yookassa import Configuration, Payment
from django.conf import settings
import uuid

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


# Configure Yookassa credentials properly so client selects correct auth type.
secret = getattr(settings, 'YOOKASSA_SECRET_KEY', None) or getattr(settings, 'YOOKASSA_SHOP_KEY', None)
auth_token = getattr(settings, 'YOOKASSA_AUTH_TOKEN', None)
shop_id = getattr(settings, 'YOOKASSA_SHOP_ID', None)

if auth_token:
    Configuration.configure_auth_token(auth_token)
elif shop_id and secret:
    Configuration.configure(shop_id, secret)
else:
    raise RuntimeError('YOOKASSA credentials are not configured. Set YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY or YOOKASSA_AUTH_TOKEN in settings.')

def create_payment(request, product_id):
    product = Product.objects.get(id=product_id)

    payment = Payment.create({
        "amount": {
            "value": str(product.price),
            "currency": "KZT"
        },
        "confirmation": {
        "type": "redirect",
        "return_url": "http://127.0.0.1:8000/payment-success/"
        },
        "capture": True,
        "description": f"Оплата {product.name}"
    }, str(uuid.uuid4()))  # обязательно str(uuid4())

    payment_id = payment.id  # берём id платежа
    Order.objects.create(
        Product=product,
        payment_id=payment_id,
        status="pending"
    )

    # Render a confirmation page with continuation button instead of immediate redirect.
    return render(request, 'create_payment.html', {
        'confirmation_url': payment.confirmation.confirmation_url,
        'product': product,
    })

def payment_success(request):
    return render(request, "payment_success.html")


def create_payment_cart(request):
    """Create a payment for all items in the user's cart (or session cart)."""
    # Gather items and calculate total
    items = []
    total = 0

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.all()
        for it in cart_items:
            items.append(it)
            total += int(it.get_total_price())
    else:
        session_cart = request.session.get('cart', {})
        for pid, qty in session_cart.items():
            try:
                product = Product.objects.get(id=pid)
            except Product.DoesNotExist:
                continue
            total_price = int(product.price) * qty
            items.append({
                'product': product,
                'quantity': qty,
                'total_price': total_price,
            })
            total += total_price

    if total == 0:
        return redirect('view_cart')

    payment = Payment.create({
        "amount": {
            "value": str(total),
            "currency": "KZT"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "http://127.0.0.1:8000/payment-success/"
        },
        "capture": True,
        "description": "Оплата корзины"
    }, str(uuid.uuid4()))

    payment_id = payment.id

    # create Order rows for each product in the cart
    for it in items:
        if isinstance(it, dict):
            product = it['product']
        else:
            product = it.product

        Order.objects.create(
            Product=product,
            payment_id=payment_id,
            status='pending'
        )

    return render(request, 'create_payment.html', {
        'confirmation_url': payment.confirmation.confirmation_url,
        'items': items,
        'total_price': total,
    })

# ---------- AUTH ----------

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})



def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("product_list")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


# ---------- STORE ----------

def product_list(request):
    products = Product.objects.all()
    return render(request, "store/product_list.html", {
        "products": products
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "store/product_detail.html", {
        "product": product
    })


def about(request):
    return render(request, "store/about.html")


# ---------- CART ----------

def view_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        items = cart.items.all()
        total_price = sum(item.get_total_price() for item in items)

        return render(request, "cart/cart.html", {
            "cart": cart,
            "items": items,
            "total_price": total_price,
        })
    else:
        session_cart = request.session.get('cart', {})
        items = []
        total_price = 0
        for pid, qty in session_cart.items():
            try:
                product = Product.objects.get(id=pid)
            except Product.DoesNotExist:
                continue
            total = int(product.price) * qty
            items.append({
                'product': product,
                'quantity': qty,
                'total_price': total,
            })
            total_price += total

        return render(request, "cart/cart.html", {
            "cart": None,
            "items": items,
            "total_price": total_price,
        })


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": 1}
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()
    else:
        cart = request.session.get('cart', {})
        key = str(product_id)
        cart[key] = cart.get(key, 0) + 1
        request.session['cart'] = cart

    return redirect("view_cart")


def cart_sidebar(request):
    """Return cart HTML fragment for offcanvas sidebar."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        items = cart.items.all()
        total_price = sum(item.get_total_price() for item in items)
        # Provide items as CartItem objects for the template
        context = {
            'items': items,
            'total_price': total_price,
        }
    else:
        session_cart = request.session.get('cart', {})
        items = []
        total_price = 0
        for pid, qty in session_cart.items():
            try:
                product = Product.objects.get(id=pid)
            except Product.DoesNotExist:
                continue
            total = int(product.price) * qty
            items.append({
                'product': product,
                'quantity': qty,
                'total_price': total,
            })
            total_price += total

        context = {
            'items': items,
            'total_price': total_price,
        }

    return render(request, 'cart/_cart_sidebar.html', context)
