from django.core.validators import FileExtensionValidator
from django.db import models


class Collection(models.Model):
    title = models.CharField(
        'Title',
        max_length=200
    )

    def __str__(self):
        return self.title


class Ebook(models.Model):
    file = models.FileField(
        'File',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )

    collection = models.ForeignKey(
        'library.Collection',
        verbose_name='Collection',
        related_name='ebooks',
        on_delete=models.CASCADE
    )
