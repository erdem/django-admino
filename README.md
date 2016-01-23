# Admino

Admino django admin'i customize eden bir python paketidir. 

### Problem?
Django admin development sürecinde test yapmak için çok iyi çözümdür. Ancak panelde son kullanıcıya göre özel çözümler yaparken, genel admin yapısının dışına çıkmadan customize yapmanız gerekir. 

Yapacağınız bazı custom çözümler, admin'nin template dosyalarının çok karışık olması, static dosyalarının yetersizliği ve birçok "ModelAdmin" class'nin methodlarını override etmeniz gerektiğinden, fazlasıyla yorucu olabilir. 

Bu sorunu çözmek için django'nun admin uygulamasını extend edip, template ve static dosyaları ekleyrek bunu çözen paketler mevcuttur. 

[django-suit](https://github.com/darklow/django-suit){: target=_blank}
[django-jet](https://github.com/geex-arts/django-jet){: target=_blank}

Bu çözümler django'nun "ModelAdmin" class'i üzerinde bir değişiklik yapamadıkları için, admin de özel çözüm getirmek bir yere kadar çözülüyor.

### Çözüm

Django admin discover pattern'i ile tüm "admin.py" dosylarınızı load ederken, araya girip, kendi custom "ModelAdmin" mixin class'ini ekler. Bu işlem için "admin.py" dosyalarınızda bir değişiklik yapmanız gerekmez.

Bu şekilde Admino içinde gelen bir çok çözümü admin sayfalarında kullabilir. Bunun yanında kendi kullanacağınız mixin class'i kullanabilirsiniz. 

Front-end tarafında yapacağınız çözümler, Admino ile birlikte gelen REST API kullanabilirsiniz. 

#### REST API NASIL ÇALIŞIYOR?

Built-in API admin de ki list ve detail kullanılan model datasını json olarak verir. Bu şekilde sadece javascript kullanarak tüm django uygulamalarında ki datalara ulaşabilirsiniz. 

##### EXAMPLE:

**Visible Books list page url:** /admin/books/book/?is_visible__exact=1

![](http://oi67.tinypic.com/2dqkfbs.jpg)

**Visible Books api url:** /admin/books/book/**api**/?is_visible__exact=1

![](http://oi65.tinypic.com/dwp5i.jpg)


**Book detail page url:** /admin/books/book/1/

![](http://oi67.tinypic.com/2sbvhmx.jpg)


**Book detail api url:** /admin/books/**api**/book/1/

![](http://oi66.tinypic.com/zxlkc6.jpg)


#### Install
Admio çalışması için "INSTALLED_APPS" listesinin en başında olmalı.
    
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

    import admino
    admin.site = admino.site.activated(admin.site)
    
    urlpatterns = [
        url(r'^admin/', admin.site.urls),
    ]


Add custom admin Mixin class:

settigns.py

    ADMINO_MIXIN_CLASS = "app.module.AdminMixinClass"
    

    





