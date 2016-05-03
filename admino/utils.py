import importlib

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


def obj_as_dict(o):
    if isinstance(o, dict):
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
