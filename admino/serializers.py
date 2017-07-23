from marshmallow import Schema


class ModelSchema(Schema):

    def dump(self, obj, many=None, update_fields=True, **kwargs):
        return super(ModelSchema, self).dump(obj, many, update_fields, **kwargs)
