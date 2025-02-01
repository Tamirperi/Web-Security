"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from users.views import register
from django.shortcuts import render  # נדרש עבור ה-URL של מסך הצלחה
from users.views import add_customer
from users.views import login_view
from users.views import change_password
from users.views import forgot_password
from users.views import reset_password
from users.views import customer_list
from users.views import update_customer
from users.views import delete_customer
from users.views import delete_user
from users.views import logout_view 


def home_view(request):
    return render(request, 'users/home.html')  # נטען את ה-HTML המתאים

urlpatterns = [
    path('', home_view, name='home'),  # דף הבית
    path('admin/', admin.site.urls),  # כתובת ללוח הבקרה
    path('register/', register, name='register'),  # כתובת למסך רישום
    path('success/', lambda request: render(request, 'users/success.html'), name='success'),  # מסך הצלחה
    path('add-customer/', add_customer, name='add_customer'),  # כתובת להוספת לקוח
    path('customer-success/', lambda request: render(request, 'users/customer_success.html'), name='customer_success'),  # מסך הצלחה ללקוח
    path('login/', login_view, name='login'), # כתובת למסך התחברות
    path('change-password/', change_password, name='change_password'),  # כתובת לשינוי סיסמה
    path('password-success/', lambda request: render(request, 'users/password_success.html'), name='password_success'),  # מסך הצלחה
    path('forgot-password/', forgot_password, name='forgot_password'),  # כתובת לשכחת סיסמה
    path('reset-password/', reset_password, name='reset_password'),  # כתובת לאיפוס סיסמה
    path('customers/', customer_list, name='customer_list'),  # כתובת לרשימת לקוחות
    path('update-customer/<int:customer_id>/', update_customer, name='update_customer'),  # כתובת לעדכון לקוח
    path('delete-customer/<int:customer_id>/', delete_customer, name='delete_customer'),  # כתובת למחיקת לקוח
    path('delete-user/<int:user_id>/', delete_user, name='delete_user'),
    path('logout/', logout_view, name='logout'),


] 