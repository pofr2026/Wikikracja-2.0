# Third party imports
from django.test import TestCase

# Local folder imports
from chat.forms import RoomForm
from chat.models import Room


class RoomFormTest(TestCase):
    def test_valid_form(self):
        form = RoomForm(data={"title": "NowyPokój"})
        self.assertTrue(form.is_valid())

    def test_different_case_title_is_allowed(self):
        Room.objects.create(title="Duplikat")
        form = RoomForm(data={"title": "duplikat"})
        self.assertTrue(form.is_valid())

    def test_duplicate_title_exact_case(self):
        Room.objects.create(title="Duplikat")
        form = RoomForm(data={"title": "Duplikat"})
        self.assertFalse(form.is_valid())

    def test_empty_title_invalid(self):
        form = RoomForm(data={"title": ""})
        self.assertFalse(form.is_valid())

    def test_title_too_long_invalid(self):
        form = RoomForm(data={"title": "A" * 256})
        self.assertFalse(form.is_valid())
