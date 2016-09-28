from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static

from django.contrib import admin as django_admin
import admino

admino.site.activated()

urlpatterns = [
    url(r'^admin/', admino.site.urls),
    url(r'^django-admin/', django_admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
