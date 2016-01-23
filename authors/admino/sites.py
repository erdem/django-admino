from collections import OrderedDict
from functools import update_wrapper
import json
from urllib import urlencode
from django import http
from django.conf import settings
from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.admin.options import IncorrectLookupParameters
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse_lazy
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

    def get_admin_cl(self, request):
        ChangeList = self.get_changelist(request)
        try:
            cl = ChangeList(request, self.model, self.list_display,
                self.list_display_links, self.list_filter, self.date_hierarchy,
                self.search_fields, self.list_select_related, self.list_per_page,
                self.list_max_show_all, self.list_editable, self)
            return cl

        except IncorrectLookupParameters:
            raise Exception("IncorrectLookupParameters")

    def obj_as_dict(self, request, obj):
        bundle = dict()
        model_fields = self.model._meta.get_all_field_names()
        readonly_fields = self.get_readonly_fields(request, obj)
        model_fields.extend(readonly_fields)
        model_fields.extend(self.list_display)

        for field in model_fields:
            if hasattr(obj, field):
                bundle[field] = getattr(obj, field)

            if hasattr(self, field):
                field_method = getattr(self, field)
                if callable(field_method):
                    bundle[field] = field_method(obj)
                else:
                    bundle[field] = field_method

        return bundle

    def get_api_next_url(self, request, cl):
        page_num = cl.page_num
        if page_num and page_num is not int or not cl.multi_page:
            return None
        info = self.model._meta.app_label, self.model._meta.model_name
        url = reverse_lazy("admin:%s_%s_api_list" % info)
        host = request.get_host()
        params = cl.params
        params["p"] = page_num + 1
        return "%s://%s%s?%s" % (request.scheme, host, url, urlencode(params))

    def get_api_previous_url(self, request, cl):
        page_num = cl.page_num
        if page_num == 0 or not cl.multi_page:
            return None

        info = self.model._meta.app_label, self.model._meta.model_name
        url = reverse_lazy("admin:%s_%s_api_list" % info)
        host = request.get_host()
        params = cl.params
        params["p"] = page_num - 1
        return "%s://%s%s?%s" % (request.scheme, host, url, urlencode(params))

    def api_list(self, request, *args, **kwargs):
        cl = self.get_admin_cl(request)
        results = []
        for obj in cl.result_list:
            results.append(self.obj_as_dict(request, obj))

        data = OrderedDict()
        data["count"] = cl.result_count
        data["next"] = self.get_api_next_url(request, cl)
        data["previous"] = self.get_api_previous_url(request, cl)
        data["results"] = results
        return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json")

    def api_detail(self, request, *args, **kwargs):
        obj = self.get_object(request, object_id=kwargs.get("pk"))
        ModelForm = self.get_form(request, obj=obj)
        form = ModelForm(instance=obj)
        data = self.obj_as_dict(request, form.instance)
        return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    def api_create(self, request, *args, **kwargs):
        data = json.loads(request.body)

        ModelForm = self.get_form(request, obj=None)
        form = ModelForm(data=data, files=request.FILES)
        if form.is_valid():
            form.save()
            data = self.obj_as_dict(request, obj=None)
            return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json")
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
