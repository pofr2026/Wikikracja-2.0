# Third party imports
from django.test import TestCase

# Local folder imports
from chat.forms import RoomForm
from chat.models import Room


class RoomFormTest(TestCase):
    def test_valid_form(self):
        form = RoomForm(data={"title": "NowyPokój"})
        self.assertTrue(form.is_valid())

    def test_duplicate_title_different_case_is_rejected(self):
        Room.objects.create(title="Duplikat")
        form = RoomForm(data={"title": "duplikat"})
        self.assertFalse(form.is_valid())

    def test_duplicate_title_polish_non_ascii_is_rejected(self):
        # SQLite's LIKE/iexact only case-folds ASCII; Polish letters like Ś/ś, Ż/ż
        # slip through. Validation must use Python casefold, not DB-level iexact.
        Room.objects.create(title="Środa")
        form = RoomForm(data={"title": "środa"})
        self.assertFalse(form.is_valid())

    def test_rename_to_same_title_different_case_is_allowed(self):
        # editing own room: 'Ogólny' → 'ogólny' must not block itself
        room = Room.objects.create(title="Ogólny")
        form = RoomForm(data={"title": "ogólny"}, instance=room)
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
