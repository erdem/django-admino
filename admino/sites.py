import json

from functools import update_wrapper
from admino.utils import import_from_string
from admino.views import ChangeListRetrieveAPIView

from django import http
from django.conf import settings
from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.admin.options import IncorrectLookupParameters
from django.conf.urls import url, include
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .constants import HTTP_METHOD_VIEWS


class AdminoMixin(ModelAdmin):

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

    def obj_as_dict(self, request, obj):
        # todo implement a serializer class
        bundle = dict()
        model_fields = self.model._meta.get_fields()

        field_names = [f.name for f in model_fields]
        readonly_fields = self.get_readonly_fields(request, obj)
        field_names.extend(readonly_fields)
        field_names.extend(self.list_display)

        for field in model_fields:
            if field.rel and field.rel.many_to_many:
                data = []
                rel_model = field.rel.model
                f_val = getattr(obj, field.name)
                rel_field_names = [f.name for f in rel_model._meta.get_fields() if not f.is_relation]
                for m in f_val.all():
                    d = dict()
                    for f_name in rel_field_names:
                        d[f_name] = getattr(m, f_name)
                    data.append(d)
                bundle[field.name] = data
                field_names.remove(field.name)

        for field in field_names:
            if hasattr(obj, field):
                f = getattr(obj, field)
                bundle[field] = unicode(f)

            if hasattr(self, field):
                field_method = getattr(self, field)
                if callable(field_method):
                    bundle[field] = field_method(obj)
                else:
                    bundle[field] = field_method

        info = self.model._meta.app_label, self.model._meta.model_name
        admin_detail_url = reverse_lazy("admin:%s_%s_change" % info, args=(obj.id,))
        bundle["detail_page"] = str(admin_detail_url)
        return bundle

    def get_api_list_view_class(self):
        return ChangeListRetrieveAPIView

    def api_list(self, request, *args, **kwargs):
        cl = self.get_admin_cl(request)
        view_class = self.get_api_list_view_class()
        print view_class
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

