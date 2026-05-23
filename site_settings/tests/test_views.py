import os
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from site_settings.models import SiteSettings
from site_settings.tests.utils import make_branding_png


class SiteSettingsBrandingUploadViewTest(TestCase):
    """Test 5 (TDD red): view site_admin obsługuje POST z brand_mark/brand_mark_dark."""

    def setUp(self):
        self.tmp_media = tempfile.mkdtemp(prefix='wikikracja_test_media_')
        self.override = override_settings(MEDIA_ROOT=self.tmp_media)
        self.override.enable()

        User = get_user_model()
        self.user = User.objects.create_user(username='admin', password='testpass123')
        self.client.force_login(self.user)
        self.url = reverse('site_admin')

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.tmp_media, ignore_errors=True)

    def test_post_uploads_brand_mark_and_redirects(self):
        response = self.client.post(self.url, {
            'save_branding': '1',
            'brand_mark': make_branding_png(),
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(bool(SiteSettings.get().brand_mark))

    def test_post_uploads_brand_mark_dark_and_redirects(self):
        response = self.client.post(self.url, {
            'save_branding': '1',
            'brand_mark_dark': make_branding_png(),
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(bool(SiteSettings.get().brand_mark_dark))

    def test_post_uploads_both_marks_at_once(self):
        response = self.client.post(self.url, {
            'save_branding': '1',
            'brand_mark': make_branding_png(),
            'brand_mark_dark': make_branding_png(),
        })
        self.assertEqual(response.status_code, 302)
        ss = SiteSettings.get()
        self.assertTrue(bool(ss.brand_mark))
        self.assertTrue(bool(ss.brand_mark_dark))

    def test_post_with_invalid_image_does_not_save(self):
        invalid = SimpleUploadedFile('bad.png', b'not really a png', content_type='image/png')
        self.client.post(self.url, {
            'save_branding': '1',
            'brand_mark': invalid,
        })
        # view nie crashuje, niepoprawny plik nie zapisuje się
        self.assertFalse(bool(SiteSettings.get().brand_mark))

    def test_post_uploads_branding_text(self):
        response = self.client.post(self.url, {
            'save_branding': '1',
            'branding_text': 'Wspólnota Słoneczna',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SiteSettings.get().branding_text, 'Wspólnota Słoneczna')


class SiteSettingsBrandingRemoveViewTest(TestCase):
    """Test 6 (TDD red): POST z <field>-clear=on usuwa wgrany brand mark + cleanup derivatives."""

    def setUp(self):
        self.tmp_media = tempfile.mkdtemp(prefix='wikikracja_test_media_')
        self.override = override_settings(MEDIA_ROOT=self.tmp_media)
        self.override.enable()

        User = get_user_model()
        self.user = User.objects.create_user(username='admin', password='testpass123')
        self.client.force_login(self.user)
        self.url = reverse('site_admin')

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.tmp_media, ignore_errors=True)

    def _upload_brand_mark(self):
        ss = SiteSettings.get()
        ss.brand_mark = make_branding_png()
        ss.save()
        return ss

    def test_post_clear_brand_mark_removes_field(self):
        self._upload_brand_mark()
        self.assertTrue(bool(SiteSettings.get().brand_mark))

        response = self.client.post(self.url, {
            'save_branding': '1',
            'brand_mark-clear': 'on',
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(bool(SiteSettings.get().brand_mark))

    def test_post_clear_brand_mark_dark_removes_field(self):
        ss = SiteSettings.get()
        ss.brand_mark_dark = make_branding_png()
        ss.save()
        self.assertTrue(bool(SiteSettings.get().brand_mark_dark))

        response = self.client.post(self.url, {
            'save_branding': '1',
            'brand_mark_dark-clear': 'on',
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(bool(SiteSettings.get().brand_mark_dark))

    def test_post_clear_brand_mark_does_not_remove_brand_mark_dark(self):
        ss = SiteSettings.get()
        ss.brand_mark = make_branding_png()
        ss.brand_mark_dark = make_branding_png()
        ss.save()

        self.client.post(self.url, {
            'save_branding': '1',
            'brand_mark-clear': 'on',
        })

        ss = SiteSettings.get()
        self.assertFalse(bool(ss.brand_mark))
        self.assertTrue(bool(ss.brand_mark_dark))

    def test_post_clear_brand_mark_removes_derivatives_from_disk(self):
        self._upload_brand_mark()
        derived_dir = os.path.join(settings.MEDIA_ROOT, 'site_branding', 'derived')
        # sanity: derivatives wygenerowane po uploadzie
        self.assertTrue(os.path.exists(os.path.join(derived_dir, 'favicon.ico')))

        self.client.post(self.url, {
            'save_branding': '1',
            'brand_mark-clear': 'on',
        })

        # po clear: derivative files NIE istnieją na dysku
        for filename in ('favicon.ico', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png'):
            path = os.path.join(derived_dir, filename)
            self.assertFalse(os.path.exists(path), f'{filename} should be deleted after clear')


class SidebarBrandMarkRenderingTest(TestCase):
    """Test 7 (TDD red): sidebar i topbar renderują <img brand-mark> gdy brand_mark istnieje."""

    def setUp(self):
        self.tmp_media = tempfile.mkdtemp(prefix='wikikracja_test_media_')
        self.override = override_settings(MEDIA_ROOT=self.tmp_media)
        self.override.enable()

        User = get_user_model()
        self.user = User.objects.create_user(username='admin', password='testpass123')
        self.client.force_login(self.user)
        self.url = reverse('home')

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.tmp_media, ignore_errors=True)

    def test_renders_fallback_fa_icon_when_no_brand_mark(self):
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('fa-building-columns', content)
        self.assertNotIn('class="brand-mark"', content)

    def test_renders_img_brand_mark_when_brand_mark_exists(self):
        ss = SiteSettings.get()
        ss.brand_mark = make_branding_png()
        ss.save()

        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        # <img brand-mark> obecne (sidebar + topbar; konkretna liczba zależy od theme switching — test 8)
        self.assertIn('class="brand-mark', content)
        # fallback FA ikona już nie renderowana
        self.assertNotIn('fa-building-columns', content)
        # URL z MEDIA_URL
        self.assertIn('/media/site_branding/', content)

    def test_sidebar_shows_branding_text_when_set(self):
        ss = SiteSettings.get()
        ss.branding_text = 'Wspólnota Słoneczna'
        ss.save()
        response = self.client.get(self.url)
        self.assertIn('Wspólnota Słoneczna', response.content.decode('utf-8'))

    def test_sidebar_does_not_show_branding_text_when_empty(self):
        response = self.client.get(self.url)
        self.assertNotIn('Wspólnota Słoneczna', response.content.decode('utf-8'))

    def test_title_uses_branding_text_when_set(self):
        ss = SiteSettings.get()
        ss.branding_text = 'Wspólnota Słoneczna'
        ss.save()
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn('<title>Wspólnota Słoneczna</title>', content)

    def test_title_fallbacks_to_request_site_name_when_branding_text_empty(self):
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        # Django Sites default to "example.com" — niezależnie od konkretnej wartości,
        # NIE powinno być "Wspólnota Słoneczna" (które byłoby z branding_text)
        self.assertNotIn('<title>Wspólnota Słoneczna</title>', content)
        self.assertIn('<title>', content)


class BrandMarkThemeFallbackTest(TestCase):
    """Test 8 (TDD red): rendering brand-mark-light + brand-mark-dark + fallback gdy jedno pole puste."""

    def setUp(self):
        self.tmp_media = tempfile.mkdtemp(prefix='wikikracja_test_media_')
        self.override = override_settings(MEDIA_ROOT=self.tmp_media)
        self.override.enable()

        User = get_user_model()
        self.user = User.objects.create_user(username='admin', password='testpass123')
        self.client.force_login(self.user)
        self.url = reverse('home')

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.tmp_media, ignore_errors=True)

    def test_renders_both_classes_when_both_marks_uploaded(self):
        ss = SiteSettings.get()
        ss.brand_mark = make_branding_png(color=(255, 0, 0, 255))
        ss.brand_mark_dark = make_branding_png(color=(0, 0, 255, 255))
        ss.save()

        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        # po 2 wystąpienia każdej klasy (sidebar + topbar)
        self.assertEqual(content.count('brand-mark-light'), 2)
        self.assertEqual(content.count('brand-mark-dark'), 2)

    def test_dark_img_fallbacks_to_brand_mark_when_dark_field_empty(self):
        ss = SiteSettings.get()
        ss.brand_mark = make_branding_png()
        ss.save()

        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        # oba <img> tagi obecne
        self.assertEqual(content.count('brand-mark-light'), 2)
        self.assertEqual(content.count('brand-mark-dark'), 2)
        # oba używają tego samego URL'a (brand_mark) → 4 wystąpień (2 sidebar + 2 topbar)
        self.assertEqual(content.count(ss.brand_mark.url), 4)

    def test_light_img_fallbacks_to_brand_mark_dark_when_light_field_empty(self):
        ss = SiteSettings.get()
        ss.brand_mark_dark = make_branding_png()
        ss.save()

        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        self.assertEqual(content.count('brand-mark-light'), 2)
        self.assertEqual(content.count('brand-mark-dark'), 2)
        # oba używają brand_mark_dark URL'a
        self.assertEqual(content.count(ss.brand_mark_dark.url), 4)


class ManifestAndAppleTouchIconBrandTest(TestCase):
    """Test 9 (TDD red): manifest icons + apple-touch-icon link używają derivatives gdy brand_mark istnieje."""

    def setUp(self):
        self.tmp_media = tempfile.mkdtemp(prefix='wikikracja_test_media_')
        self.override = override_settings(MEDIA_ROOT=self.tmp_media)
        self.override.enable()

        User = get_user_model()
        self.user = User.objects.create_user(username='admin', password='testpass123')
        self.client.force_login(self.user)

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.tmp_media, ignore_errors=True)

    def test_manifest_uses_static_fallback_without_brand_mark(self):
        response = self.client.get(reverse('manifest'))
        srcs = [icon['src'] for icon in response.json()['icons']]
        self.assertTrue(all('/static/home/images/' in src for src in srcs))

    def test_manifest_uses_media_derivatives_with_brand_mark(self):
        ss = SiteSettings.get()
        ss.brand_mark = make_branding_png()
        ss.save()

        response = self.client.get(reverse('manifest'))
        srcs = [icon['src'] for icon in response.json()['icons']]
        self.assertEqual(sum('/media/site_branding/derived/' in s for s in srcs), 3)
        self.assertFalse(any('/static/home/images/' in s for s in srcs))

    def test_apple_touch_icon_link_uses_static_fallback_without_brand_mark(self):
        response = self.client.get(reverse('home'))
        content = response.content.decode('utf-8')
        self.assertIn('rel="apple-touch-icon"', content)
        self.assertIn('/static/home/images/favicon.ico', content)

    def test_apple_touch_icon_link_uses_media_with_brand_mark(self):
        ss = SiteSettings.get()
        ss.brand_mark = make_branding_png()
        ss.save()

        response = self.client.get(reverse('home'))
        content = response.content.decode('utf-8')
        self.assertIn('rel="apple-touch-icon"', content)
        self.assertIn('/media/site_branding/derived/apple-touch-icon.png', content)

    def test_favicon_link_uses_static_fallback_without_brand_mark(self):
        response = self.client.get(reverse('home'))
        content = response.content.decode('utf-8')
        self.assertIn('rel="icon"', content)
        self.assertIn('/static/home/images/favicon.ico', content)

    def test_favicon_link_uses_media_with_brand_mark(self):
        ss = SiteSettings.get()
        ss.brand_mark = make_branding_png()
        ss.save()

        response = self.client.get(reverse('home'))
        content = response.content.decode('utf-8')
        self.assertIn('rel="icon"', content)
        self.assertIn('/media/site_branding/derived/favicon.ico', content)


class CacheBustVersioningTest(TestCase):
    """Test 10 (TDD red): URL-e brandowych assetów mają ?v=<timestamp> dla cache-bust."""

    def setUp(self):
        self.tmp_media = tempfile.mkdtemp(prefix='wikikracja_test_media_')
        self.override = override_settings(MEDIA_ROOT=self.tmp_media)
        self.override.enable()

        User = get_user_model()
        self.user = User.objects.create_user(username='admin', password='testpass123')
        self.client.force_login(self.user)

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.tmp_media, ignore_errors=True)

    def test_brand_mark_url_in_template_has_version_param(self):
        ss = SiteSettings.get()
        ss.brand_mark = make_branding_png()
        ss.save()

        response = self.client.get(reverse('home'))
        content = response.content.decode('utf-8')
        expected_ts = str(int(ss.updated_at.timestamp()))
        self.assertIn(f'{ss.brand_mark.url}?v={expected_ts}', content)

    def test_manifest_media_icons_have_version_param(self):
        ss = SiteSettings.get()
        ss.brand_mark = make_branding_png()
        ss.save()

        response = self.client.get(reverse('manifest'))
        srcs = [icon['src'] for icon in response.json()['icons']]
        expected_ts = str(int(ss.updated_at.timestamp()))
        self.assertTrue(all(f'?v={expected_ts}' in src for src in srcs))

    def test_manifest_static_fallback_has_no_version_param(self):
        response = self.client.get(reverse('manifest'))
        srcs = [icon['src'] for icon in response.json()['icons']]
        self.assertFalse(any('?v=' in src for src in srcs))

    def test_apple_touch_icon_link_has_version_param_with_brand_mark(self):
        ss = SiteSettings.get()
        ss.brand_mark = make_branding_png()
        ss.save()

        response = self.client.get(reverse('home'))
        content = response.content.decode('utf-8')
        expected_ts = str(int(ss.updated_at.timestamp()))
        self.assertIn(f'apple-touch-icon.png?v={expected_ts}', content)


class WikikracjaVersionLineTest(TestCase):
    """Test 11 (TDD red): sidebar logo-sub zawiera 'Wikikracja v.X.Y.Z' (powered-by linijka)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='admin', password='testpass123')
        self.client.force_login(self.user)

    def test_sidebar_logo_sub_contains_powered_by_wikikracja_and_version(self):
        from django.conf import settings as django_settings
        response = self.client.get(reverse('home'))
        content = response.content.decode('utf-8')
        expected = f'Wikikracja v.{django_settings.APP_VERSION}'
        self.assertIn(expected, content)


class SiteAdminBrandingFormUITest(TestCase):
    """Test 12 (TDD red): /site-settings/ pokazuje kartę Branding z formularzem upload'u."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='admin', password='testpass123')
        self.client.force_login(self.user)
        self.url = reverse('site_admin')

    def test_site_admin_renders_branding_form_with_file_inputs(self):
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        # form z multipart (wymagany dla file upload)
        self.assertIn('enctype="multipart/form-data"', content)
        # dyskryminator handler'a
        self.assertIn('name="save_branding"', content)
        # input file dla obu pól
        self.assertIn('name="brand_mark"', content)
        self.assertIn('name="brand_mark_dark"', content)
        self.assertIn('type="file"', content)

    def test_site_admin_renders_branding_text_input(self):
        response = self.client.get(self.url)
        self.assertIn('name="branding_text"', response.content.decode('utf-8'))

    def test_site_admin_renders_brand_mark_thumbnail_when_set(self):
        # tearDown isolated tmp_media; trzeba podpiąć temporary media tu
        with tempfile.TemporaryDirectory(prefix='wikikracja_test_media_') as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                ss = SiteSettings.get()
                ss.brand_mark = make_branding_png()
                ss.save()
                response = self.client.get(self.url)
                self.assertIn('class="brand-mark-preview"', response.content.decode('utf-8'))

    def test_site_admin_does_not_render_thumbnail_without_brand_mark(self):
        response = self.client.get(self.url)
        self.assertNotIn('class="brand-mark-preview"', response.content.decode('utf-8'))

    def test_brand_mark_thumbnail_is_clickable_link_to_full_image(self):
        with tempfile.TemporaryDirectory(prefix='wikikracja_test_media_') as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                ss = SiteSettings.get()
                ss.brand_mark = make_branding_png()
                ss.save()
                response = self.client.get(self.url)
                content = response.content.decode('utf-8')
                # thumbnail wrapped in <a target="_blank"> with link to media URL
                self.assertRegex(content, r'<a[^>]+href="/media/site_branding/[^"]+"[^>]*target="_blank"')
