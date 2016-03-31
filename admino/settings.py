import importlib


def import_from_string(setting_path):
    """
    Attempt to import a class from a string representation.
    """
    try:
        parts = setting_path.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        msg = "Could not import '%s' for Admino setting '%s'" % setting_name
        raise ImportError(msg)