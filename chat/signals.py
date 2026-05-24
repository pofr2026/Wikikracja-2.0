from django.db.models import F
from django.db.models.functions import Greatest
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

user_accepted = Signal()
user_deleted = Signal()


@receiver(post_save, sender='chat.Message')
def _sync_room_last_message(sender, instance, created, **kwargs):
    # Denormalizujemy ostatnią wiadomość do Room, żeby sidebar mógł renderować podgląd bez JOIN-a.
    # Tylko przy CREATE — edycja istniejącej wiadomości nie powinna zmieniać "ostatniej" semantyki.
    # last_activity przez Greatest() — nigdy nie cofamy czasu (room mógł być bumpowany później przez inną akcję).
    if not created:
        return
    from chat.models import Room
    Room.objects.filter(id=instance.room_id).update(
        last_message_text=instance.text[:200],
        last_message_sender_id=instance.sender_id,
        last_message_at=instance.time,
        last_message_anonymous=instance.anonymous,
        last_activity=Greatest(F('last_activity'), instance.time),
    )
