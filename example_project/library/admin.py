from django.contrib import admin
from dragndrop_related.views import DragAndDropRelatedImageMixin

from .models import Collection, Ebook


class EbookInline(admin.StackedInline):
    extra = 0
    model = Ebook


@admin.register(Collection)
class CollectionAdmin(DragAndDropRelatedImageMixin, admin.ModelAdmin):
    dropzone_accepted_files = 'application/pdf'
    inlines = [EbookInline]
    related_manager_field_name = 'ebooks'
    related_model_field_name = 'file'
