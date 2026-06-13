from django.urls import path

from . import views

urlpatterns = [
    path("offers/<int:pk>/accept", views.accept_offer),
    path("offers/<int:pk>/decline", views.decline_offer),
]
