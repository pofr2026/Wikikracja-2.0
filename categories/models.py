from django.db import models


class AbstractCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    is_protected = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
