import json
from functools import update_wrapper

from admino.serializers import ModelSchema
from admino.utils import import_from_string
from admino.views import ChangeListRetrieveAPIView, LoginAPIView

from django import http
from django.conf import settings
from django.conf.urls import url, include
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.contrib.admin import actions
from django.contrib.admin import site as django_site
from django.contrib.admin import AdminSite as DjangoAdminSite, ModelAdmin as DjangoModelAdmin, autodiscover as django_admin_autodiscover
from django.contrib.admin.options import IncorrectLookupParameters

from .constants import HTTP_METHOD_VIEWS


class AdminoMixin(DjangoModelAdmin):
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options', 'trace']
    api_schema = ModelSchema

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
                wrap(self.admin_site.admin_view(self.api_admin_meta_view)),
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

    def get_model_serializer_fields(self):
        field_names = []
        for field in self.model._meta.get_fields():
            if not field.is_relation:
                field_names.append(field.name)
        return field_names

    def get_serializer_fields(self, request, obj=None):
        model_fields = self.get_model_serializer_fields()
        return model_fields

    def serialize_obj(self, request, obj):
        serializer_fields = self.get_serializer_fields(request, obj)

        class ObjSchema(self.api_schema):
            class Meta:
                fields = serializer_fields

        schema = ObjSchema()
        data, errors = schema.dump(obj)
        return data

    def get_api_list_view_class(self):
        return ChangeListRetrieveAPIView

    def api_admin_meta_view(self, request, *args, **kwargs):
        meta_data = {
            "list_per_page": self.list_per_page,
            "list_max_show_all": self.list_max_show_all
        }
        return JsonResponse(meta_data)

    def api_list(self, request, *args, **kwargs):
        cl = self.get_admin_cl(request)
        view_class = self.get_api_list_view_class()
        return view_class().get(request, model_admin=self, admin_cl=cl)

    def api_detail(self, request, *args, **kwargs):
        obj = self.get_object(request, object_id=kwargs.get("pk"))
        data = self.serialize_obj(request, obj)
        return JsonResponse(data)

    def api_create(self, request, *args, **kwargs):
        data = json.loads(request.body)

        ModelForm = self.get_form(request, obj=None)
        form = ModelForm(data=data, files=request.FILES)
        if form.is_valid():
            obj = form.save()
            data = self.serialize_obj(request, obj)
            return JsonResponse(data)
        else:
            errors = {
                "errors": json.loads(form.errors.as_json())
            }
            return JsonResponse(errors, status=400)

    def api_update(self, request, *args, **kwargs):
        return HttpResponse("put")

    def api_delete(self, request, *args, **kwargs):
        return HttpResponse("delete")


class ModelAdmino(AdminoMixin, DjangoModelAdmin):
    admin_type = "admino"


class AdminoSite(DjangoAdminSite):

    def __init__(self, django_site, name='admino'):
        self.django_site = django_site
        self._registry = {}
        self.name = name
        self._actions = {'delete_selected': actions.delete_selected}
        self._global_actions = self._actions.copy()

    def activated(self):
        django_admin_registered_apps = self.django_site._registry
        for model, admin_obj in django_admin_registered_apps.items():
            mixin_class = AdminoMixin
            if hasattr(settings, "ADMINO_MIXIN_CLASS"):
                module_path = getattr(settings, "ADMINO_MIXIN_CLASS")
                mixin_class = import_from_string(module_path)
            django_admin_class = admin_obj.__class__
            admino_class = type("ModelAdmino", (mixin_class, django_admin_class), {"admin_type": "admino"})
            admino_obj = admino_class(model, self)
            self._registry[model] = admino_obj

        django_admin_autodiscover()
        return self

    def get_urls(self):
        urlpatterns = super(AdminoSite, self).get_urls()
        valid_app_labels = []
        default_api_urls = [
            url(r'^api/login/$', self.api_login, name='api_login'),
            # url(r'^logout/$', wrap(self.logout), name='logout'),
            # url(r'^password_change/$', wrap(self.password_change, cacheable=True), name='password_change'),
        ]
        urlpatterns = urlpatterns + default_api_urls
        for model, model_admin in self._registry.items():
            api_urlpatterns = [
                url(r'^api/%s/%s/' % (model._meta.app_label, model._meta.model_name), include(model_admin.api_urls)),
            ]
            urlpatterns = urlpatterns + api_urlpatterns
            if model._meta.app_label not in valid_app_labels:
                valid_app_labels.append(model._meta.app_label)

        return urlpatterns

    def api_login(self, request, *args, **kwargs):
        return LoginAPIView.as_view()(request, *args, **kwargs)

site = AdminoSite(django_site=django_site)


