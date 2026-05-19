from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class WspolnotaCalendarTileTest(TestCase):
    """Kafelek kalendarza na stronie wspólnoty powinien być linkiem do /events/."""

    def setUp(self):
        self.user = User.objects.create_user(username='testowy', password='pass')
        self.client.login(username='testowy', password='pass')

    def test_calendar_tile_title_links_to_events_list(self):
        """Tytuł sekcji Calendar jest elementem <a> prowadzącym do events:list."""
        response = self.client.get(reverse('obywatele:wspolnota'))
        self.assertEqual(response.status_code, 200)
        events_url = reverse('events:list')
        # href="/events/" bez fragmentu — tak rozróżniamy od linków do konkretnych dni
        self.assertContains(response, f'href="{events_url}"')
