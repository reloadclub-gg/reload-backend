from django.urls import path

from . import views

app_name = 'websocket'

urlpatterns = [
    path('docs/', views.docs, name='docs'),
]
