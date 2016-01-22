from functools import update_wrapper
from django import http
from django.conf import settings
from django.conf.urls import patterns, url
from django.contrib.admin import AdminSite, ModelAdmin
from django.core import serializers
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


class AdminoMixin(object):

    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options', 'trace']

    def get_urls(self):
        from django.conf.urls import url
        import ipdb;ipdb.set_trace()
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            url(r'^api/$',
                csrf_exempt(wrap(self.admin_site.admin_view(self.api_list_view))),
                name='%s_%s_api_list' % info),
            url(r'^api/(?P<id>[-\d]+)/$',
                csrf_exempt(wrap(self.admin_site.admin_view(self.api_detail_view))),
                name='%s_%s_api_detail' % info),
            url(r'^$', wrap(self.changelist_view), name='%s_%s_changelist' % info),
            url(r'^add/$', wrap(self.add_view), name='%s_%s_add' % info),
            url(r'^(.+)/history/$', wrap(self.history_view), name='%s_%s_history' % info),
            url(r'^(.+)/delete/$', wrap(self.delete_view), name='%s_%s_delete' % info),
            url(r'^(.+)/change/$', wrap(self.change_view), name='%s_%s_change' % info),
            # For backwards compatibility (was the change url before 1.9)
            # url(r'^(.+)/$', wrap(RedirectView.as_view(
            #     pattern_name='%s:%s_%s_change' % ((self.admin_site.name,) + info)
            # ))),
        ]
        return urlpatterns

    def _allowed_methods(self):
        return [m.upper() for m in self.http_method_names if hasattr(self, "api_" + m)]

    def http_method_not_allowed(self, request, *args, **kwargs):
        if settings.DEBUG and self._allowed_methods():
            raise Exception("Only" + str(self._allowed_methods()))
        return http.HttpResponseNotAllowed(self._allowed_methods())

    @csrf_exempt
    def api_list_view(self, request, *args, **kwargs):
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, "api_" + request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        return handler(request, *args, **kwargs)

    def api_get(self, request, *args, **kwargs):
        data = serializers.serialize("json", self.queryset(request))
        return HttpResponse(data, mimetype="application/json")

    @csrf_exempt
    def api_post(self, request, *args, **kwargs):
        return HttpResponse("post")

    @csrf_exempt
    def api_put(self, request, *args, **kwargs):
        return HttpResponse("put")

    @csrf_exempt
    def api_delete(self, request, *args, **kwargs):
        return HttpResponse("delete")

    def api_detail_view(self, request, *args, **kwargs):
        return HttpResponse("detail")


def mixin_factory(name, base_class, mixin):
    return type(name, (base_class, mixin), {"admin_type": "admino"})


class ModelAdmino(AdminoMixin, ModelAdmin):
    admin_type = "admino"


class AdminoSite(AdminSite):

    def register(self, model_or_iterable, admin_class=None, **options):
        if getattr(admin_class, "admin_type", "") != "admino":
            admin_class = mixin_factory("AdminoModelAdmin", AdminoMixin, admin_class)
        return super(AdminoSite, self).register(model_or_iterable, admin_class, **options)

site = AdminoSite()
