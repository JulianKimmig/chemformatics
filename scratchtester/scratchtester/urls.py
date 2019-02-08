"""djangobase URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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

from scratchtester import views, consumer

app_name = "scratchtester"
urlpatterns = [
    path("", views.MainPage.as_view()),
    path(
        "measurement/<int:id>/tabbed",
        views.MeasurementTabbed.as_view(),
        name="measurmenttabbed",
    ),
    path(
        "measurement/<int:id>/<option>",
        views.MeasurementView.as_view(),
        name="measurment",
    ),
    path("measurement/<int:id>/<data>", views.MeasurementView.as_view(), name="image"),
    path("data/<int:id>/<data>", views.MeasurementData.as_view(), name="get_data"),
    path("data/<int:id>/<data>", views.MeasurementData.as_view(), name="post_data"),
]

websockets = [path("ws", consumer.BaseConsumer)]
