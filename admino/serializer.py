from collections import OrderedDict

from django.utils import six


class SerializerMetaclass(type):

    @classmethod
    def _get_declared_fields(cls, bases, attrs):
        pass

    def __new__(cls, name, bases, attrs):
        attrs["fields"] = cls._get_declared_fields(bases, attrs)
        return super(SerializerMetaclass, cls).__new__(cls, name, bases, attrs)


@six.add_metaclass(SerializerMetaclass)
class BaseSerializer(object):
    def __init__(self, admin_instance, *args, **kwargs):
        pass
