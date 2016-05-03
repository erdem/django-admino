from collections import OrderedDict


class FormWidgetSerializer(object):

    def __init__(self, widget, *args, **kwargs):
        self.widget = widget

    @property
    def data(self):
        widget_data = OrderedDict()
        widget_data["type"] = self.field.__class__.__name__
        return widget_data


class FormFieldSerializer(object):

    def __init__(self, field, *args, **kwargs):
        self.field = field

    @property
    def data(self):
        field_data = OrderedDict()
        field_data["type"] = self.field.__class__.__name__
        field_data["widget"] = self.serialize_widget()
        field_data["is_required"] = self.field.required
        return field_data

    def serialize_widget(self):
        return FormWidgetSerializer(self.field.widget).data