# Placeholder — testy WebSocket consumers
#
# Wymagają: pip install channels[daphne] i konfiguracji InMemoryChannelLayer w settings.
# Uruchomienie: python manage.py test chat.tests.test_consumers
#
# Przykładowy szkielet (odkomentuj gdy gotowy do implementacji):
#
# import secrets
# from channels.testing import WebsocketCommunicator
# from django.contrib.auth.models import User
# from django.test import TransactionTestCase
# from django.test.utils import override_settings
# from zzz.asgi import application
# from chat.models import Room
#
# CHANNEL_LAYERS_TEST = {
#     "default": {
#         "BACKEND": "channels.layers.InMemoryChannelLayer",
#     }
# }
#
# @override_settings(CHANNEL_LAYERS=CHANNEL_LAYERS_TEST)
# class ChatConsumerTest(TransactionTestCase):
#     async def test_connect_authenticated(self):
#         ...
#
#     async def test_send_message(self):
#         ...
#
#     async def test_join_room_unauthorized(self):
#         ...
