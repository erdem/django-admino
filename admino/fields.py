from collections import OrderedDict

from admino.utils import obj_as_dict


class BaseSerializer(object):
    pass


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


class ModelAdminSerializer(BaseSerializer):

    def __init__(self, model_admin, admin_form, *args, **kwargs):
        self.model_admin = model_admin
        self.admin_form = admin_form

    @property
    def data(self):
        return {
            "form": self.serialize_form()
        }

    def serialize_form(self):
        return FormSerializer(self.admin_form).data
