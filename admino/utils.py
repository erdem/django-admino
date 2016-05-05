import importlib

from admino.serializers import FormSerializer
from django.forms import BaseForm
from django.utils.functional import Promise
from django.utils.encoding import force_unicode


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
