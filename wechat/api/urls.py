from django.urls import path
from api.views import Services


urlpatterns = [
    path('', Services.as_view()),
]