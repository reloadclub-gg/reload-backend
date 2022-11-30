from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from .api.routes import api

admin.site.site_header = 'GTA MM Admin'
admin.site.enable_nav_sidebar = False

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path("api/", api.urls),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
