from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _


class AdminoModel(models.Model):

    class Meta:
        app_label = 'tests'
        abstract = True


class BasicModel(AdminoModel):
    text = models.CharField(
        max_length=255,
        verbose_name=_("Text Field"),
        help_text=_("Text description.")
    )


# Related Fields Test Models

class ForeignKeyTarget(AdminoModel):
    name = models.CharField(max_length=255, verbose_name=_("Name"))


class ForeignKeySource(AdminoModel):
    target = models.ForeignKey(ForeignKeyTarget)
    description = models.CharField(max_length=255, blank=True)


class NullForeignKeySource(AdminoModel):
    target = models.ForeignKey(ForeignKeyTarget, blank=True, null=True,
                               related_name='nullable_sources',
                               verbose_name='Optional target object',
                               on_delete=models.CASCADE)
    description = models.CharField(max_length=255)


class ManyToManyTarget(AdminoModel):
    name = models.CharField(max_length=255, verbose_name=_("Name"))


class ManyToManySource(AdminoModel):
    name = models.CharField(max_length=255)
    targets = models.ManyToManyField(ManyToManyTarget, related_name='sources')


class NullManyToManySource(AdminoModel):
    name = models.CharField(max_length=255)
    targets = models.ManyToManyField(ManyToManyTarget, blank=True, related_name='nullable_sources')


class OneToOneTarget(AdminoModel):
    name = models.CharField(max_length=255)


class OneToOneSource(AdminoModel):
    target = models.OneToOneField(OneToOneTarget)
    description = models.CharField(max_length=255)


class NullOneToOneSource(AdminoModel):
    target = models.OneToOneField(OneToOneTarget, blank=True, null=True,
                                  related_name='nullable_source', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)


# Individual Fields Test Models

