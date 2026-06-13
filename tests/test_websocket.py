"""Testy integracyjne WebSocket dla ChatConsumer.

Pokrywają: rejekcję anonymous, sukces auth, join public/private, send w/bez join,
multi-user broadcast, invalid reaction, get-notifications-data.
"""
import asyncio

import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser

from chat.models import Room
from tests.factories import UserFactory
from zzz.routing import application


async def _consume_initial(communicator):
    """Po connect ChatConsumer wysyła {unread_count}. Zjadamy żeby kolejne receive zwracało odpowiedź na nasze polecenie."""
    await communicator.receive_json_from()


@pytest.fixture
def public_room_with_user(db):
    user = UserFactory(username='wsuser', email='ws@example.com')
    room = Room.objects.create(title='WS Public Room', public=True)
    return user, room


@pytest.fixture
def private_room_with_users(db):
    member = UserFactory(username='wsmember', email='member@example.com')
    nonmember = UserFactory(username='wsnonmember', email='nonmember@example.com')
    room = Room.objects.create(title='WS Private Room', public=False, protected=False)
    room.allowed.add(member)
    return member, nonmember, room


@pytest.mark.django_db(transaction=True)
async def test_anonymous_user_rejected():
    """Anonymous user nie może otworzyć WS — connect zwraca False."""
    communicator = WebsocketCommunicator(application, "/chat/stream/")
    communicator.scope['user'] = AnonymousUser()
    connected, _ = await communicator.connect()
    assert connected is False


@pytest.mark.django_db(transaction=True)
async def test_authenticated_user_receives_unread_count(public_room_with_user):
    """Auth user po connect dostaje {unread_count: N} jako pierwszą wiadomość."""
    user, _ = public_room_with_user
    communicator = WebsocketCommunicator(application, "/chat/stream/")
    communicator.scope['user'] = user
    connected, _ = await communicator.connect()
    assert connected is True

    response = await communicator.receive_json_from()
    assert 'unread_count' in response
    assert isinstance(response['unread_count'], int)

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_join_public_room_returns_metadata(public_room_with_user):
    """Join public room zwraca {join: room_id, title, public, notifications}."""
    user, room = public_room_with_user
    communicator = WebsocketCommunicator(application, "/chat/stream/")
    communicator.scope['user'] = user
    connected, _ = await communicator.connect()
    assert connected is True
    await _consume_initial(communicator)

    await communicator.send_json_to({"command": "join", "room_id": room.id})
    response = await communicator.receive_json_from()

    assert response.get('join') == str(room.id)
    assert response.get('title') == 'WS Public Room'
    assert response.get('public') is True
    assert 'notifications' in response

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_join_private_room_as_nonmember_denied(private_room_with_users):
    """Nie-członek próbujący wejść do private room dostaje {error: ACCESS_DENIED}."""
    _member, nonmember, room = private_room_with_users
    communicator = WebsocketCommunicator(application, "/chat/stream/")
    communicator.scope['user'] = nonmember
    connected, _ = await communicator.connect()
    assert connected is True
    await _consume_initial(communicator)

    await communicator.send_json_to({"command": "join", "room_id": room.id})
    response = await communicator.receive_json_from()

    assert response.get('error') == 'ACCESS_DENIED'

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_send_to_unjoined_room_denied(public_room_with_user):
    """Send do pokoju bez wcześniejszego join dostaje {error: ROOM_ACCESS_DENIED}."""
    user, room = public_room_with_user
    communicator = WebsocketCommunicator(application, "/chat/stream/")
    communicator.scope['user'] = user
    connected, _ = await communicator.connect()
    assert connected is True
    await _consume_initial(communicator)

    await communicator.send_json_to({
        "command": "send",
        "room_id": room.id,
        "message": "Hello",
        "is_anonymous": False,
        "attachments": {}
    })
    response = await communicator.receive_json_from()

    assert response.get('error') == 'ROOM_ACCESS_DENIED'

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_invalid_reaction_rejected(public_room_with_user):
    """message-react z nieprawidłową reakcją dostaje {error: INVALID_REACTION}."""
    user, room = public_room_with_user
    communicator = WebsocketCommunicator(application, "/chat/stream/")
    communicator.scope['user'] = user
    connected, _ = await communicator.connect()
    assert connected is True
    await _consume_initial(communicator)

    from chat.models import Message
    message = await sync_to_async(Message.objects.create)(sender=user, text='Test', room=room, anonymous=False)

    await communicator.send_json_to({
        "command": "message-react",
        "reaction": "invalid_reaction_xyz",
        "message_id": message.id
    })
    response = await communicator.receive_json_from()

    assert response.get('error') == 'INVALID_REACTION'

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_get_notifications_data_returns_rooms(public_room_with_user):
    """Komenda get-notifications-data zwraca odpowiedź z polem 'rooms'."""
    user, _ = public_room_with_user
    communicator = WebsocketCommunicator(application, "/chat/stream/")
    communicator.scope['user'] = user
    connected, _ = await communicator.connect()
    assert connected is True
    await _consume_initial(communicator)

    await communicator.send_json_to({"command": "get-notifications-data"})
    response = await communicator.receive_json_from()

    assert 'rooms' in response

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_multi_user_broadcast(private_room_with_users):
    """Wiadomość od user1 dociera przez channel layer do user2 obecnego w tym samym pokoju."""
    member, nonmember, room = private_room_with_users
    await sync_to_async(room.allowed.add)(nonmember)

    comm1 = WebsocketCommunicator(application, "/chat/stream/")
    comm1.scope['user'] = member
    connected, _ = await comm1.connect()
    assert connected is True
    await _consume_initial(comm1)

    comm2 = WebsocketCommunicator(application, "/chat/stream/")
    comm2.scope['user'] = nonmember
    connected, _ = await comm2.connect()
    assert connected is True
    await _consume_initial(comm2)

    await comm1.send_json_to({"command": "join", "room_id": room.id})
    await comm1.receive_json_from()
    await comm2.send_json_to({"command": "join", "room_id": room.id})
    await comm2.receive_json_from()

    await comm1.send_json_to({
        "command": "send",
        "room_id": room.id,
        "message": "Hello from member",
        "is_anonymous": False,
        "attachments": {}
    })

    # User2 może dostać kilka różnych eventów (online_data, unread_count update) przed właściwą wiadomością.
    # Czytamy do skutku (max 10 wiadomości / timeout 1s każda) i szukamy konkretnej treści.
    found = False
    for _ in range(10):
        try:
            response = await comm2.receive_json_from(timeout=1)
        except Exception:
            break
        if 'Hello from member' in str(response):
            found = True
            break

    assert found, "User2 nie otrzymał broadcast'u 'Hello from member' od user1"

    await comm1.disconnect()
    await comm2.disconnect()


async def _drain(communicator, predicate, tries=8):
    """Czyta eventy do skutku, zwraca pierwszy spelniajacy predicate (albo None).
    Lapie tylko timeout (brak kolejnego eventu) — szerszy except maskowalby realne bledy."""
    for _ in range(tries):
        try:
            response = await communicator.receive_json_from(timeout=1)
        except (asyncio.TimeoutError, TimeoutError):
            return None
        if predicate(response):
            return response
    return None


async def _quiet_disconnect(*communicators):
    """Disconnect ignorujac CancelledError z wiszacego _post_send_processing (tlo).
    CancelledError dziedziczy z BaseException (nie Exception) — stad szeroki except."""
    for c in communicators:
        try:
            await c.disconnect()
        except BaseException:
            pass


async def _setup_sender_recipient(member, nonmember, room):
    """Wspolny setup testow room_added: nadawca (w pokoju) + odbiorca (online, NIE w pokoju).
    Zwraca (sender, recipient) gotowe; nadawca po join, odbiorca CELOWO bez join."""
    await sync_to_async(room.allowed.add)(nonmember)

    sender = WebsocketCommunicator(application, "/chat/stream/")
    sender.scope['user'] = member
    assert (await sender.connect())[0] is True
    await _consume_initial(sender)

    recipient = WebsocketCommunicator(application, "/chat/stream/")
    recipient.scope['user'] = nonmember
    assert (await recipient.connect())[0] is True
    await _consume_initial(recipient)

    await sender.send_json_to({"command": "join", "room_id": room.id})
    await sender.receive_json_from()
    return sender, recipient


async def _send_text(sender, room, text):
    await sender.send_json_to({
        "command": "send",
        "room_id": room.id,
        "message": text,
        "is_anonymous": False,
        "attachments": {},
    })


@pytest.mark.django_db(transaction=True)
async def test_first_message_emits_room_added_to_absent_recipient(private_room_with_users):
    """Pierwsza wiadomosc w prywatnym pokoju → odbiorca online ale NIE bedacy w pokoju
    dostaje room_added z gotowym HTML kafelka (zawiera username nadawcy)."""
    member, nonmember, room = private_room_with_users
    sender, recipient = await _setup_sender_recipient(member, nonmember, room)

    await _send_text(sender, room, "Pierwsza wiadomosc")

    event = await _drain(recipient, lambda r: 'room_added' in r)
    assert event is not None, "Odbiorca nie dostal room_added po 1. wiadomosci"
    payload = event['room_added']
    assert payload['room_id'] == room.id
    # HTML kafelka renderowany serwerowo z room_link.html — niesie nazwe nadawcy (other_user dla odbiorcy).
    assert member.username in payload['html']
    assert 'room-link' in payload['html']

    await _quiet_disconnect(sender, recipient)


@pytest.mark.django_db(transaction=True)
async def test_muted_recipient_gets_room_added_but_no_notification(private_room_with_users):
    """P2=(A): mute tlumi tylko alert. Odbiorca z wyciszonym pokojem DOSTAJE room_added
    (kafelek musi sie pojawic), ale NIE dostaje notification."""
    member, nonmember, room = private_room_with_users
    await sync_to_async(room.muted_by.add)(nonmember)
    sender, recipient = await _setup_sender_recipient(member, nonmember, room)

    await _send_text(sender, room, "Do wyciszonego")

    got_room_added = await _drain(recipient, lambda r: 'room_added' in r)
    assert got_room_added is not None, "Wyciszony odbiorca tez musi dostac kafelek (room_added)"

    # Po room_added nie powinno przyjsc notification dla wyciszonego pokoju.
    got_notification = await _drain(recipient, lambda r: 'notification' in r, tries=3)
    assert got_notification is None, "Wyciszony pokoj nie powinien generowac notification"

    await _quiet_disconnect(sender, recipient)


@pytest.mark.django_db(transaction=True)
async def test_second_message_does_not_reemit_room_added(private_room_with_users):
    """room_added leci tylko dla PIERWSZEJ wiadomosci (count==1). Druga juz nie —
    inaczej kazda kolejna wiadomosc do nieobecnego usera dublowalaby kafelek."""
    member, nonmember, room = private_room_with_users
    # Pokoj ma juz historie — ta wiadomosc NIE jest pierwsza.
    from chat.models import Message
    await sync_to_async(Message.objects.create)(sender=member, text='stara', room=room, anonymous=False)

    sender, recipient = await _setup_sender_recipient(member, nonmember, room)

    await _send_text(sender, room, "Druga wiadomosc")

    event = await _drain(recipient, lambda r: 'room_added' in r)
    assert event is None, "room_added nie powinien lecie dla kolejnej wiadomosci (tylko 1. wiadomosc)"

    await _quiet_disconnect(sender, recipient)
