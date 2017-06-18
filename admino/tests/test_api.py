from django.test import TestCase


class DummyTestCase(TestCase):

    def test_settings(self):
        self.assertEqual(2+2, 4)