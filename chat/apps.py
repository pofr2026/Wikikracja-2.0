from django.apps import AppConfig


class ChatConfig(AppConfig):
    name = 'chat'

    def ready(self):
        # Import signals to register them
        import chat.signals  # noqa: F401
