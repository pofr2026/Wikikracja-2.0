from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from chat.services import get_avatar_url
from chat.tests.utils import make_user


class _UserWithoutProfile:
    """Stub user where accessing .uzytkownik raises (simulating broken/missing relation)."""
    @property
    def uzytkownik(self):
        raise AttributeError("no related profile")


class GetAvatarUrlTest(TestCase):
    def test_returns_none_when_avatar_not_uploaded(self):
        # post_save signal auto-creates Uzytkownik; avatar field is empty by default.
        user = make_user("noavatar")
        self.assertIsNone(get_avatar_url(user))

    def test_returns_none_when_user_is_none(self):
        self.assertIsNone(get_avatar_url(None))

    def test_returns_none_when_uzytkownik_attribute_raises(self):
        self.assertIsNone(get_avatar_url(_UserWithoutProfile()))

    def test_returns_url_when_avatar_uploaded(self):
        user = make_user("withavatar")
        user.uzytkownik.avatar = SimpleUploadedFile(
            "test.png", b"fake-bytes", content_type="image/png"
        )
        user.uzytkownik.save()
        result = get_avatar_url(user)
        self.assertIsNotNone(result)
        self.assertIn("avatars/", result)
        self.assertTrue(result.endswith(".png"))
