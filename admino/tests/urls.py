from django.conf.urls import url
from django.contrib import admin

import admino

admin.site = admino.site.activated()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
]
