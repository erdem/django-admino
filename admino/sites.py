import json
from collections import OrderedDict

from functools import update_wrapper

from admino.utils import import_from_string
from admino.views import ChangeListRetrieveAPIView, APIMetaView

from django import http
from django.conf import settings
from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.admin.options import IncorrectLookupParameters
from django.conf.urls import url, include
from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .constants import HTTP_METHOD_VIEWS


class AdminoMixin(object):
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options', 'trace']

    def get_api_urls(self):

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            url(r'^$',
                wrap(self.admin_site.admin_view(self.dispatch)),
                name='%s_%s_api_list' % info),
            url(r'^(?P<pk>[-\d]+)/$',
                wrap(self.admin_site.admin_view(self.dispatch)),
                name='%s_%s_api_detail' % info),
            url(r'^meta/$',
                wrap(self.admin_site.admin_view(self.api_meta_view)),
                name='%s_%s_api_meta' % info),
        ]
        return urlpatterns

    def api_urls(self):
        return self.get_api_urls()

    api_urls = property(api_urls)

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

    def get_api_readonly_fields(self, request, obj):
        model_fields = self.model._meta.get_fields()
        model_field_names = [f.name for f in model_fields]
        modal_admin_fields = set(list(self.get_readonly_fields(request, obj)) + list(self.get_list_display(request)))
        api_readonly_fields = []
        for field in modal_admin_fields:
            if not field in model_field_names:
                api_readonly_fields.append(field)
        return api_readonly_fields

    def get_api_all_field_names(self, request, obj):
        api_readonly_fields = self.get_api_readonly_fields(request, obj)
        model_fields = self.model._meta.get_fields()
        field_names = [f.name for f in model_fields]
        return list(set(field_names)) + api_readonly_fields


    def serialize_objs(self, objs):
        data_objs = json.loads(serializers.serialize('json', objs)  )
        for data in data_objs:
            data.update(data["fields"])
            del data["fields"]
        return data_objs

    def serialize_obj(self, obj):
        return self.serialize_objs([obj])[0]

    def obj_as_dict(self, request, obj):
        data = self.serialize_obj(obj)
        for field in obj._meta.get_fields():
            if field.is_relation:
                field_value = getattr(obj, field.name)
                if field_value:
                    if field.many_to_many:                    
                        data[field.name] = self.serialize_objs(field_value.all())
                    elif field.many_to_one or field.one_to_one or field_value.one_to_many:
                        data[field.name] = self.serialize_obj(field_value)
        return data


    def get_api_list_view_class(self):
        return ChangeListRetrieveAPIView

    def api_meta_view(self, request, *args, **kwargs):
        return APIMetaView().get(request, model_admin=self)

    def api_list(self, request, *args, **kwargs):
        cl = self.get_admin_cl(request)
        view_class = self.get_api_list_view_class()
        return view_class().get(request, model_admin=self, admin_cl=cl)

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
            obj = form.save()
            data = self.obj_as_dict(request, obj)
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
            mixin_class = AdminoMixin
            if hasattr(settings, "ADMINO_MIXIN_CLASS"):
                module_path = getattr(settings, "ADMINO_MIXIN_CLASS")
                mixin_class = import_from_string(module_path)
            django_admin_class = admin_obj.__class__
            admino_class = type("ModelAdmino", (mixin_class, django_admin_class), {"admin_type": "admino"})
            admino_obj = admino_class(model, self)
            self._registry[model] = admino_obj
        return self

    def get_urls(self):
        urlpatterns = super(AdminoSite, self).get_urls()
        valid_app_labels = []
        for model, model_admin in self._registry.items():
            api_urlpatterns = [
                url(r'^api/%s/%s/' % (model._meta.app_label, model._meta.model_name), include(model_admin.api_urls)),
            ]
            urlpatterns = urlpatterns + api_urlpatterns
            if model._meta.app_label not in valid_app_labels:
                valid_app_labels.append(model._meta.app_label)
        return urlpatterns


site = AdminoSite()

