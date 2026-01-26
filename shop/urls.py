from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    if request.user.is_authenticated:
        return HttpResponse(f'Привет {request.user.username}')
    return HttpResponse("Вы вошли")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
]