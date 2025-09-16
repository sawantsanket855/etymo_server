"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from etymo.api import check_connection,get_word_data,login_api,register_api,sendOTP_api, sendPasswordResetEmail_api, updatePassword_api,verifyOTP_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('check_connection/', check_connection),
    path('get_word_data/',get_word_data),
    path('login/',login_api),
    path('register/',register_api),
    path('send_otp/',sendOTP_api),
    path('verify_otp/',verifyOTP_api),
    path('update_password/',updatePassword_api),
    path('send_password_reset_email/',sendPasswordResetEmail_api),
    
]
