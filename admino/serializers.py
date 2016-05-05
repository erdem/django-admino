from collections import OrderedDict
from django.forms.forms import DeclarativeFieldsMetaclass

from django import forms
from django.utils.encoding import force_unicode
from django.utils.functional import Promise


def obj_as_dict(o):

    if isinstance(o, DeclarativeFieldsMetaclass):
        o = FormSerializer(form=o).data

    if isinstance(o, forms.Field):
        o = FormFieldSerializer(field=o).data

    if isinstance(o, forms.Widget):
        o = FormWidgetSerializer(widget=o).data

    if isinstance(o, (list, tuple)):
        o = [obj_as_dict(x) for x in o]

    if isinstance(o, Promise):
        try:
            o = force_unicode(o)
        except:
            # Item could be a lazy tuple or list
            try:
                o = [obj_as_dict(x) for x in o]
            except:
                raise Exception('Unable to resolve lazy object %s' % o)
    if callable(o):
        o = o()

    if isinstance(o, dict):
        for k, v in o.items():
            o[k] = obj_as_dict(v)

    return o


class BaseSerializer(object):
    @property
    def data(self):
        raise NotImplementedError


class FormWidgetSerializer(BaseSerializer):
    def __init__(self, widget, *args, **kwargs):
        self.widget = widget

    @property
    def data(self):
        widget_data = OrderedDict()
        widget_data["type"] = self.widget.__class__.__name__
        return widget_data


class FormFieldSerializer(BaseSerializer):
    def __init__(self, field, *args, **kwargs):
        self.field = field

    @property
    def data(self):
        field_data = OrderedDict()
        field_data["type"] = self.field.__class__.__name__
        field_data["widget"] = self.field.widget
        field_data["is_required"] = self.field.required
        return field_data


class FormSerializer(BaseSerializer):
    def __init__(self, form, *args, **kwargs):
        self.form = form

    @property
    def data(self):
        form_fields = []
        for name, field in self.form.base_fields.items():
            d = dict()
            d[name] = field
            form_fields.append(d)
        return form_fields


#todo check  "formfield_overrides"
MODEL_ADMIN_CLASS_ATTRIBUTES = (
    "raw_id_fields", "fields", "exclude", "fieldsets", "filter_vertical", "filter_horizontal", "radio_fields",
    "prepopulated_fields",  "readonly_fields", "ordering", "view_on_site",
    "show_full_result_count", "list_display", "list_display_links", "list_filter", "list_per_page", "list_max_show_all",
    "list_editable", "search_fields", "date_hierarchy","save_as", "save_on_top")


class ModelAdminSerializer(BaseSerializer):
    def __init__(self, model_admin, admin_form, *args, **kwargs):
        self.model_admin = model_admin
        self.admin_form = admin_form

    @property
    def data(self):
        data = OrderedDict()
        for attr in MODEL_ADMIN_CLASS_ATTRIBUTES:
            data[attr] = getattr(self.model_admin, attr, None)
        data["form"] = self.admin_form
        return obj_as_dict(data)

    def serialize_form(self):
        return FormSerializer(self.admin_form).data
