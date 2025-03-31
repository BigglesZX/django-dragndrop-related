from django import forms
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import models, transaction
from django.db.models import Max
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseRedirect)
from django.urls import re_path, reverse
from django.views.generic import DetailView
from django.views.generic.edit import FormMixin, ProcessFormView
from django.conf import settings


class DragAndDropView(PermissionRequiredMixin, FormMixin, ProcessFormView,
                      DetailView):
    ''' Define a generic view used to handle POST requests from the Dropzone
        library. The `model` will be injected dynamically by the `ModelAdmin`
        when defining the custom route with `get_urls`
    '''

    def get(self, request, *args, **kwargs):
        ''' Catch GET requests and redirect them to the `change` view for the
            model instance
        '''

        self.object = self.get_object()
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpattern = 'admin:{0}_{1}_change'.format(*info)
        return HttpResponseRedirect(
            reverse(urlpattern, kwargs={'object_id': self.object.pk}))

    def get_form_class(self):
        ''' Construct a dynamic form class with a field named using the
            `related_model_field_name` kwarg passed in from the `ModelAdmin`,
            and with a type appropriate to the underlying field on the related
            model

            source: https://stackoverflow.com/a/27505090/258794
        '''

        related_manager_field_name = \
            self.kwargs['related_manager_field_name']
        related_model_field_name = \
            self.kwargs['related_model_field_name']
        related_model = \
            getattr(self.object, related_manager_field_name).field.model
        related_model_field_class = \
            related_model._meta.get_field(related_model_field_name)

        form_fields = {}
        form_fields[related_model_field_name] = \
            forms.ImageField() if isinstance(related_model_field_class, models.ImageField) else forms.FileField()  # noqa: E501

        return type('DragAndDropForm', (forms.Form,), form_fields)

    def get_permission_required(self):
        ''' Ensure the user has `change` permission for the model '''

        info = self.model._meta.app_label, self.model._meta.model_name
        return ('{0}.change_{1}'.format(*info), )

    def post(self, request, *args, **kwargs):
        ''' Make sure the `object` is available when handling POSTs (necessary
            due to the composition of this class)
        '''

        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        ''' Create a new instance of the related model via the related manager
            of this view's model. Use the supplied `related_model_field_name`
            as the field name when creating the instance.
        '''

        related_manager_field_name = \
            self.kwargs['related_manager_field_name']
        related_model_field_name = \
            self.kwargs['related_model_field_name']
        related_model_order_field_name = \
            self.kwargs['related_model_order_field_name']

        file = self.request.FILES.get(related_model_field_name)
        related_manager = getattr(self.object, related_manager_field_name)

        with transaction.atomic():
            add_kwargs = {}
            add_kwargs[related_model_field_name] = file

            if related_model_order_field_name:
                aggregation_name = f'{related_model_order_field_name}__max'
                order = \
                    (related_manager.aggregate(
                        Max(related_model_order_field_name))
                        [aggregation_name] or 0) + 1
                add_kwargs[related_model_order_field_name] = order

            related_manager.create(**add_kwargs)

        return HttpResponse('Thanks, your file was processed')

    def form_invalid(self, form):
        ''' Combine all error messages from the form and return as the text of
            an `HttpResponseBadRequest`
        '''

        combined_message = ''
        for _, messages in form.errors.items():
            for message in messages:
                combined_message = f'{combined_message} {message}'
        return HttpResponseBadRequest(combined_message)


class DragAndDropRelatedImageMixin(object):
    ''' Define some helpful properties and methods to add our drag-and-drop UI
        to the `change` template of the associated model. Add a bunch of
        helpful info to the context of `add` or `change` views and define a
        custom route for receiving POSTed uploads.
    '''

    ''' Path to the custom admin `change_form` template '''
    change_form_template = 'admin/dragndrop_related/change_form.html'

    ''' Path to template from which the custom admin `change_form` template
        should inherit
    '''
    change_form_template_parent = 'admin/change_form.html'

    ''' Name of the reverse relation on the associated model to which images
        or files will be added
    '''
    related_manager_field_name = 'images'

    ''' Name of the field on the *related* model where images or files will
        be saved
    '''
    related_model_field_name = 'image'

    ''' Name of the ordering field on the *related* model, which will be used
        to ensure a valid order is set on new instances

        Defaults to `None` to skip this feature; override in in the descendant
        class to make use of this
    '''
    related_model_order_field_name = None

    ''' Customise the `acceptedFiles` option passed to the Dropzone library in
        the `add` or `change` templates

        Defaults to `None` to use a sensible default based on the type of the
        field on the related model
    '''
    dropzone_accepted_files = None

    ''' Determine how to load the Dropzone library

        By default the library's JS and CSS assets will be loaded from the
        UNPKG CDN. For users wanting to self-host, the
        `DRAGNDROP_RELATED_USE_STATIC_FILES` setting can be used. You will
        need to add a suitable version of `dropzone.min.js` and
        `dropzone.min.css` to your static files.
    '''
    dropzone_use_static_files = \
        getattr(settings, 'DRAGNDROP_RELATED_USE_STATIC_FILES', False)

    def get_related_model_info(self):
        ''' Access the related model according to the value of
            `related_manager_field_name` and build a dict of useful info
        '''

        related_model = \
            getattr(self.model, self.related_manager_field_name).field.model

        related_model_field_class = \
            related_model._meta.get_field(self.related_model_field_name)
        if self.dropzone_accepted_files:
            dropzone_accepted_files = self.dropzone_accepted_files
        elif isinstance(related_model_field_class, models.ImageField):
            dropzone_accepted_files = 'image/*'
        else:
            dropzone_accepted_files = None

        return {
            'related_model':
                related_model,
            'related_model_name':
                related_model._meta.verbose_name,
            'related_model_name_plural':
                related_model._meta.verbose_name_plural,
            'related_manager_field_name':
                self.related_manager_field_name,
            'related_model_field_name':
                self.related_model_field_name,
            'related_model_order_field_name':
                self.related_model_order_field_name,
            'change_form_template_parent':
                self.change_form_template_parent,
            'dropzone_accepted_files':
                dropzone_accepted_files,
            'dropzone_use_static_files':
                self.dropzone_use_static_files,
        }

    def add_view(self, request, form_url='', extra_context=None):
        ''' Add our helpful related model info to the `add` view context '''

        extra_context = extra_context or {}
        extra_context = {**extra_context, **self.get_related_model_info()}
        return super().add_view(
            request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        ''' Add our helpful related model info to the `change` view context '''

        extra_context = extra_context or {}
        extra_context = {**extra_context, **self.get_related_model_info()}
        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)

    def get_urls(self):
        ''' Define a custom route for drag-and-drop upload POSTs and attach
            our custom view to it. Pass the related model info dict to the view
            as extra `kwargs`.
        '''

        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            re_path(r'^(?P<pk>\d+)/drag-and-drop/$',
                    self.admin_site.admin_view(DragAndDropView.as_view(
                        model=self.model)),
                    self.get_related_model_info(),
                    name='{0}_{1}_drag_and_drop'.format(*info)),
        ] + super().get_urls()


class DragAndDropSingletonRelatedImageMixin(DragAndDropRelatedImageMixin):
    ''' A variation of the mixin designed for use with singleton models
        provided by `django-solo`. Ensures our `change_form` template inherits
        from django-solo's, to preserve the minor differences in the singleton
        UI.
    '''

    ''' Path to template that the custom admin `change_form` template should
        inherit from
    '''
    change_form_template_parent = 'admin/solo/change_form.html'
