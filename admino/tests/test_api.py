import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse_lazy


class LoginViewUnitTests(TestCase):

    def test_settings(self):
        USERNAME = "admin"
        PASSWORD = "password"
        EMAIL = "admin@admin.com"

        User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
        response = self.client.post(
            reverse_lazy("admino:api_login"),
            json.dumps({
                "username": USERNAME,
                "password": PASSWORD
            }),
            content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.content), {"authenticated": True})
