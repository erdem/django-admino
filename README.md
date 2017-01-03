###Django Admino (Alpha)

Admino is a django package that provides a REST API for admin endpoints. It allows you to customize django admin panel.

http://admino.io


###Problem?

Django admin is good solution for development tests and i/o, but django admin needs to be more customizable and extendable. 

### Solution:

if you want to implement a custom widget or ui for django admin, you may need a REST API to handle records.

Admino added to new api views to django admin genericly. You don't need to change default admin files. 
Every API endpoint will generate your "ModelAdmin" configurations.

##### EXAMPLE:

**Visible Books list page url:** /admin/books/book/?is_visible__exact=1

![](http://oi67.tinypic.com/2dqkfbs.jpg)

**Visible Books api url:** /admin/**api**/books/book/?is_visible__exact=1

![](http://oi65.tinypic.com/2nu3779.jpg)


**Book detail page url:** /admin/books/book/1/

![](http://oi66.tinypic.com/4jx4d0.jpg)


**Book detail api url:** /admin/**api**/books/book/1/

![](http://oi65.tinypic.com/9jisus.jpg)

#### Install

    pip install django-admino

settings.py
    
    INSTALLED_APPS = [
        'admino',
    
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
    
        'books',
    ]

urls.py
    
    from django.contrib import admin
    import admino
    
    admin.site = admino.site.activated(admin.site)
    
    urlpatterns = [
        url(r'^admin/', admin.site.urls),
    ]


Add custom admin Mixin class:

settings.py

    ADMINO_MIXIN_CLASS = "app.module.AdminMixinClass"
    
