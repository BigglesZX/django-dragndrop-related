from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from example_project.library.models import Collection


class AdminViewTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username="test", password="test")
        self.client.login(
            username="test",
            password="test",
        )
        Collection.objects.create(title="Test")

    def test_edit_view_loads_successfully(self):
        response = self.client.get(
            reverse("admin:library_collection_change", args=["1"])
        )
        self.assertEqual(response.status_code, 200)
