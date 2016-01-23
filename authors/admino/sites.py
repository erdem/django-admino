from functools import update_wrapper
import json
from django import http
from django.conf import settings
from django.contrib.admin import AdminSite, ModelAdmin
from django.core import serializers
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .constants import HTTP_METHOD_VIEWS


class AdminoMixin(ModelAdmin):

    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options', 'trace']

    def get_urls(self):
        from django.conf.urls import url
        urls = super(AdminoMixin, self).get_urls()

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            url(r'^api/$',
                wrap(self.admin_site.admin_view(self.dispatch)),
                name='%s_%s_api_list' % info),
            url(r'^api/(?P<pk>[-\d]+)/$',
                wrap(self.admin_site.admin_view(self.dispatch)),
                name='%s_%s_api_detail' % info),
        ]
        return urlpatterns + urls

    def _allowed_methods(self):
        return [m.upper() for m in self.http_method_names if hasattr(self, "api_" + m)]

    def http_method_not_allowed(self, request, *args, **kwargs):
        if settings.DEBUG and self._allowed_methods():
            raise Exception("Only" + str(self._allowed_methods()))
        return http.HttpResponseNotAllowed(self._allowed_methods())

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if not request.method.lower() in self.http_method_names:
            return self.http_method_not_allowed(request, *args, **kwargs)

        handler = self.http_method_not_allowed
        if request.method.lower() == "get":
            handler = getattr(self, "api_get", self.http_method_not_allowed)

        api_view_name = HTTP_METHOD_VIEWS.get(request.method.lower())
        if api_view_name:
            handler = getattr(self, "api_" + api_view_name, self.http_method_not_allowed)

        return handler(request, *args, **kwargs)

    def api_get(self, request, *args, **kwargs):
        if kwargs.get("pk"):
            return self.api_detail(request, *args, **kwargs)
        else:
            return self.api_list(request, *args, **kwargs)

    def api_list(self, request, *args, **kwargs):

        data = serializers.serialize("json", self.get_queryset(request))
        return HttpResponse(data, content_type="application/json")

    def changelist_view(self, request, extra_context=None):
        return super(AdminoMixin, self).changelist_view(request, extra_context)

    def api_detail(self, request, *args, **kwargs):
        obj = self.get_object(request, object_id=kwargs.get("pk"))
        ModelForm = self.get_form(request, obj=obj)
        form = ModelForm(instance=obj)
        data = self.form_as_dict(request, form)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def form_as_dict(self, request, form):
        obj = form.instance
        bundle = dict()
        form_fields = form._meta.fields
        readonly_fields = self.get_readonly_fields(request, obj)
        form_fields.extend(readonly_fields)
        for field in form_fields:
            if hasattr(obj, "id"):
                bundle["id"] = getattr(obj, "id")

            if hasattr(obj, field):
                bundle[field] = getattr(obj, field)

            if hasattr(self, field):
                bundle[field] = getattr(self, field)

        return bundle

    def api_create(self, request, *args, **kwargs):
        data = json.loads(request.body)

        ModelForm = self.get_form(request, obj=None)
        form = ModelForm(data=data, files=request.FILES)
        if form.is_valid():
            form.save()
            data = self.form_as_dict(request, form)
            return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            errors = {
                "errors": json.loads(form.errors.as_json())
            }
            return HttpResponse(json.dumps(errors), status=400, content_type="application/json")

    def api_update(self, request, *args, **kwargs):
        return HttpResponse("put")

    def api_delete(self, request, *args, **kwargs):
        return HttpResponse("delete")



class ModelAdmino(AdminoMixin, ModelAdmin):
    admin_type = "admino"


class AdminoSite(AdminSite):

    def activated(self, site_obj):
        django_admin_registered_apps = site_obj._registry
        self._registry = {}
        for model, admin_obj in django_admin_registered_apps.items():
            django_admin_class = admin_obj.__class__
            admino_class = type("ModelAdmino", (AdminoMixin, django_admin_class), {"admin_type": "admino"})
            admino_obj = admino_class(model, self)
            self._registry[model] = admino_obj
        return self

site = AdminoSite()
