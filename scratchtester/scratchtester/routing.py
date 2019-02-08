from django.urls import path

from scratchtester import consumers

urlpatterns = [path("", consumers.ChatConsumer)]
