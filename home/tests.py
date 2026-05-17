from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from chat.models import Message, Room
from home.views import FEED_CACHE_KEY, generate_feed_items


class ActivityFeedChatTest(TestCase):

    def setUp(self):
        cache.delete(FEED_CACHE_KEY)
        self.user = User.objects.create_user(username='testowy', password='pass')

    def tearDown(self):
        cache.delete(FEED_CACHE_KEY)

    def test_chat_messages_visible_for_allowed_user(self):
        room = Room.objects.create(title='Pokój testowy', public=False)
        room.allowed.add(self.user)
        Message.objects.create(sender=self.user, text='Hej!', room=room)

        feed = generate_feed_items(self.user)
        chat_items = [i for i in feed if i['content_type'] == 'room_messages']

        self.assertGreater(len(chat_items), 0, "Aktywnosc/ powinna pokazywac wiadomosci z chatu")

    def test_public_room_visible_without_allowed(self):
        room = Room.objects.create(title='Publiczny pokój', public=True)
        Message.objects.create(sender=self.user, text='Cześć!', room=room)

        feed = generate_feed_items(self.user)
        chat_items = [i for i in feed if i['content_type'] == 'room_messages']

        self.assertGreater(len(chat_items), 0, "Publiczny pokoj powinien byc widoczny bez bycia w allowed")

    def test_chat_messages_hidden_for_non_allowed_user(self):
        other_user = User.objects.create_user(username='inny', password='pass')
        room = Room.objects.create(title='Prywatny pokój', public=False)
        room.allowed.add(other_user)
        Message.objects.create(sender=other_user, text='Tajne', room=room)

        feed = generate_feed_items(self.user)
        chat_items = [i for i in feed if i['content_type'] == 'room_messages']

        self.assertEqual(len(chat_items), 0, "Uzytkownik bez dostepu nie powinien widziec pokoju")
