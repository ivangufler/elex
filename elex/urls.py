"""elex URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.contrib.auth.views import LogoutView
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf.urls import url
from django.http import HttpResponseRedirect

from . import settings

urlpatterns = []

if settings.DEBUG:
    urlpatterns.append(url(r'^admin/', admin.site.urls))

urlpatterns.extend([
    url(r'^api/v1/', include('elections.urls')),
    url(r'^auth/', include('social_django.urls')),
    url(r'^auth/logout', LogoutView.as_view(),
        {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
    url(r'^.*$', lambda request: render(request, template_name='index.html')),
])


