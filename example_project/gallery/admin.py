import admin_thumbnails

from django.contrib import admin
from dragndrop_related.views import DragAndDropRelatedImageMixin

from .models import Album, Image


@admin_thumbnails.thumbnail('image')
class ImageInline(admin.StackedInline):
    extra = 0
    model = Image


@admin.register(Album)
class AlbumAdmin(DragAndDropRelatedImageMixin, admin.ModelAdmin):
    inlines = [ImageInline]
