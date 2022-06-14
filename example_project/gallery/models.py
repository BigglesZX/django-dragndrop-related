from django.db import models


class Album(models.Model):
    title = models.CharField(
        'Title',
        max_length=200
    )

    def __str__(self):
        return self.title


class Image(models.Model):
    image = models.ImageField(
        'Image'
    )

    album = models.ForeignKey(
        'gallery.Album',
        verbose_name='Album',
        related_name='images',
        on_delete=models.CASCADE
    )
