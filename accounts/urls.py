from django.urls import include, path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', include('social_django.urls', namespace='auth')),
    path('auth/finish/', views.SteamAuthWebHook.as_view(), name='auth_finish'),
]
