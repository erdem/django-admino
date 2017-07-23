import importlib

from django.core.exceptions import ImproperlyConfigured
from marshmallow import Schema


def import_from_string(module_path):
    """
    Attempt to import a class from a string representation.
    """
    try:
        parts = module_path.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        msg = 'Could not import "%s" for Admino setting' % module_path
        raise ImportError(msg)


def modelschema_factory(model, schema=Schema, fields=None, exclude=None, strict=True, ordered=True, **kwargs):
    attrs = {'model': model}
    if fields is not None:
        attrs['fields'] = fields
    if exclude is not None:
        attrs['exclude'] = exclude

    attrs['strict'] = strict
    attrs['ordered'] = ordered

    # If parent form class already has an inner Meta, the Meta we're
    # creating needs to inherit from the parent's inner meta.
    parent = (object,)
    if hasattr(schema, 'Meta'):
        parent = (schema.Meta, object)
    Meta = type(str('Meta'), parent, attrs)

    class_name = model.__name__ + str('Schema')

    # Class attributes for the new form class.
    form_class_attrs = {
        'Meta': Meta
    }
    form_class_attrs.update(kwargs)

    if (getattr(Meta, 'fields', None) is None and
            getattr(Meta, 'exclude', None) is None):
        raise ImproperlyConfigured(
            "Calling modelschema_factory without defining 'fields' or "
            "'exclude' explicitly is prohibited."
        )

    # Instantiate type(form) in order to use the same metaclass as form.
    return type(schema)(class_name, (schema,), form_class_attrs)
