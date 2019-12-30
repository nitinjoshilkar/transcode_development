"""demo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import path,include
from .views import *
from Contido_Transcode import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', auth_view,name='auth_view'),
    path('api/add/user/', add_user,name='adduser'),
    path('api/home/', home),
    path('api/logout/', logout_view,name='logout'),
    path('api/token/', core_views.login_api,name='login_api'),
    path('api/token/refresh/', core_views.login_api_refresh,name='login_api_refresh'),
    path('api/', include('transcode.urls')),




]
