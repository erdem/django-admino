from collections import OrderedDict

from django import forms
from django.utils.encoding import force_unicode
from django.utils.functional import Promise


def obj_as_dict(o):
    if isinstance(o, forms.BaseForm):
        o = FormSerializer(form=o).data

    elif isinstance(o, forms.Field):
        o = FormFieldSerializer(field=o).data

    elif isinstance(o, forms.Widget):
        o = FormWidgetSerializer(widget=o).data

    elif isinstance(o, dict):
        for k, v in o.items():
            o[k] = obj_as_dict(v)

    elif isinstance(o, (list, tuple)):
        o = [obj_as_dict(x) for x in o]

    elif isinstance(o, Promise):
        try:
            o = force_unicode(o)
        except:
            # Item could be a lazy tuple or list
            try:
                o = [obj_as_dict(x) for x in o]
            except:
                raise Exception('Unable to resolve lazy object %s' % o)
    elif callable(o):
        o = o()

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
        return obj_as_dict(widget_data)


class FormFieldSerializer(BaseSerializer):
    def __init__(self, field, *args, **kwargs):
        self.field = field

    @property
    def data(self):
        field_data = OrderedDict()
        field_data["type"] = self.field.__class__.__name__
        field_data["widget"] = self.serialize_widget()
        field_data["is_required"] = self.field.required
        return obj_as_dict(field_data)

    def serialize_widget(self):
        return FormWidgetSerializer(self.field.widget).data


class FormSerializer(BaseSerializer):
    def __init__(self, form, *args, **kwargs):
        self.form = form

    @property
    def data(self):
        return self.serialize_fields()

    def serialize_fields(self):
        serialized_fields = []
        for name, field in self.form.base_fields.items():
            d = dict()
            d[name] = FormFieldSerializer(field=field).data
            serialized_fields.append(d)
        return serialized_fields

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
        data["form"] = self.serialize_form()
        for key, value in data.items():
            print "%s -----> %s" % (key, value)
        return obj_as_dict(data)

    def serialize_form(self):
        return FormSerializer(self.admin_form).data
