# django-dragndrop-related

Add drag-and-drop multiple uploading to any Django model where a [related model](https://docs.djangoproject.com/en/4.0/ref/models/relations/) is used to store images or files, using the awesome [Dropzone.js](https://www.dropzone.dev/js/).

![Screenshot showing widget in the Django admin](/images/upload.png)

![Screenshot showing widget in the Django admin](/images/list.png)

The example project shown uses [django-admin-thumbnails](https://pypi.org/project/django-admin-thumbnails/) to show `ImageField` preview thumbnails.

## Rationale

One of the most common requests I get from clients when working on Django projects is to support some kind of drag-and-drop upload to save them the tedium of working with multiple file upload fields. I finally put some effort into solving this problem and came up with this library, which essentially provides for the creation of related models via AJAX POST request.

It assumes some simplicity on the part of the related model – e.g. that only an `ImageField` is required to be populated – and uses [Dropzone.js](https://www.dropzone.dev/js/) to accept uploads and fire off POST requests to an endpoint which creates new child models using the related manager of the parent model.

I decided not to try to support drag-and-drop uploads when *creating* parent model instances, since the uploads would need to be stashed somewhere temporarily then associated with the new model when it was saved. Instead this library operates only on existing model instances and requires the user to reload the page once they're done dropping files, so that Django's admin/inline UI can display the newly created child models for editing. This is acceptable in my use-cases but may not be in yours.

## Compatibility

This library has been tested on Django 3.2 and 4.0 on Python 3.8, though I expect it to be fairly compatible with other versions. For now, the package is marked as requiring Python 3.6 or higher.

**Please note that this library is an early beta release, mostly published so that I can share code between my own projects. It works well for my specific use-case but your mileage may vary. If you have issues with the library please open a ticket, but be aware it's not being developed intensively at this stage.**

## Installation

```
$ pip install django-dragndrop-related
```

## Usage

Add `dragndrop_related` to your `INSTALLED_APPS` setting:

```python
INSTALLED_APPS = [
    # ...
    'dragndrop_related',
]
```

Import the mixin and apply it to your "parent" class's `ModelAdmin`:

```python
from django.contrib import admin
from dragndrop_related.views import DragAndDropRelatedImageMixin

from .models import Album, Image


''' Assuming a 'parent' model of Album and a 'child' model of Image, related
    to Album by a `ForeignKey` field (see examples below)
'''


class ImageInline(admin.StackedInline):
    extra = 0
    model = Image


@admin.register(Album)
class AlbumAdmin(DragAndDropRelatedImageMixin, admin.ModelAdmin):
    inlines = [ImageInline]
```

## Configuration

The library makes a few assumptions about your models and their relationship. Consider the following example models:

```python
class Album(models.Model):
    # ...


class Image(models.Model):
    # ...

    album = models.ForeignKey(
        'gallery.Album',
        related_name='images'
    )

    image = models.ImageField()
```

1. When adding related child instances to a parent model instance, **the library will attempt to use a related manager called `images`**. This can be overridden by specifying the `related_manager_field_name` property on the class that inherits from `DragAndDropRelatedImageMixin`, e.g.

```python
class Image(models.Model):
    # ...

    album = models.ForeignKey(
        'gallery.Album',
        related_name='album_images'
    )

class AlbumAdmin(DragAndDropRelatedImageMixin, admin.ModelAdmin):
    # ...

    related_manager_field_name = 'album_images'
```

2. **The library assumes the field on the related child model where the uploaded images/files should be saved is called `image`.** This can be overridden by specifying the `related_model_field_name` property on the class that inherits from `DragAndDropRelatedImageMixin`, e.g.

```python
class Image(models.Model):
    # ...

    album = models.ForeignKey(
        'gallery.Album',
        related_name='images'
    )

    my_image = models.ImageField()

class AlbumAdmin(DragAndDropRelatedImageMixin, admin.ModelAdmin):
    # ...

    related_model_field_name = 'my_image'
```

3. If you use an **ordering field** on your related child model, e.g. to implement [django-admin-sortable2](https://django-admin-sortable2.readthedocs.io/en/latest/), you can specify it in your `ModelAdmin` using the `related_model_order_field_name` property and `django-dragndrop-related` will set a useful value for the field when creating new related model instances. E.g.

```python
class Image(models.Model):
    # ...

    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

class AlbumAdmin(DragAndDropRelatedImageMixin, admin.ModelAdmin):
    # ...

    related_model_order_field_name = 'order'
```

## Development

If working locally on the package you can install the development tools via `pip`:

```shell
$ pip install -e .[dev]
```

Run the bundled Django example project:

```shell
$ cd example_project
$ python manage.py migrate
$ python manage.py createsuperuser
$ python manage.py runserver 0.0.0.0:8000
$ open http://localhost:8000/admin/
```

Navigate to the example `Album` model in the `Gallery` app to see the widget in action.

To lint with `flake8`:

```shell
$ flake8
```

## Issues, Suggestions, Contributions

...are welcome on GitHub. Thanks for your interest in `django-dragndrop-related`!
