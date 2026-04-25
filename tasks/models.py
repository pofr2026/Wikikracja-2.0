from django.conf import settings
from django.db import models
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL


class TaskQuerySet(models.QuerySet):
    def with_metrics(self):
        return self.annotate(
            votes_up=Count("votes", filter=Q(votes__value=TaskVote.Value.UP), distinct=True),
            votes_down=Count("votes", filter=Q(votes__value=TaskVote.Value.DOWN), distinct=True),
            votes_score=Coalesce(Sum("votes__value"), 0),
            eval_success=Count(
                "evaluations",
                filter=Q(evaluations__value=TaskEvaluation.Value.SUCCESS),
                distinct=True,
            ),
            eval_failure=Count(
                "evaluations",
                filter=Q(evaluations__value=TaskEvaluation.Value.FAILURE),
                distinct=True,
            ),
        )


class Task(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")
        REJECTED = "rejected", _("Rejected")

    class Category(models.TextChoices):
        IT = "it", _("Wikikracja i IT")
        INTERNAL = "internal", _("Sprawy Wewnętrzne LO")
        EDUCATION = "education", _("Edukacja i Wiedza")
        PROMO = "promo", _("Promocja i Zasięgi")
        RESOURCES = "resources", _("Zasoby i Biznes")
        INTERVENTION = "intervention", _("Interwencja Obywatelska")
        OTHER = "other", _("Inne")

    CATEGORY_DESCRIPTIONS = {
        "it": _("Rozwój Wikikracji, poprawki kodu, hosting, administracja techniczna."),
        "internal": _("My, nasi ludzie i zasady — onboarding, rekrutacja, powitania, spotkania."),
        "education": _("Baza wiedzy, informacje dot. DB, linki, listy, manuale."),
        "promo": _("Social media, PR, newslettery, grafika, akcje ulotkowe."),
        "resources": _("Projekty zarobkowe, składki, zarządzanie majątkiem, spółdzielnie."),
        "intervention": _("Lobbying, petycje, wdrażanie DB w gminach, kontakt z politykami."),
        "other": _("Zadania bez przypisanej kategorii."),
    }

    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    category = models.CharField(
        max_length=16,
        choices=Category.choices,
        default=Category.OTHER,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="tasks_created",
        null=True,
        blank=True,
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="tasks_assigned",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    chat_room = models.ForeignKey(
        "chat.Room",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="task",
        verbose_name=_("Chat room"),
    )

    objects = TaskQuerySet.as_manager()

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return self.title

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE

    def get_chat_room_title(self):
        return "%(title)s" % {
            "title": self.title[:90]
        }

    def get_chat_room_url(self):
        if self.chat_room_id:
            return f"{reverse('chat:chat')}#room_id={self.chat_room_id}"
        return None

    @property
    def chat_room_url(self):
        return self.get_chat_room_url()

    def get_chat_room_pulse_class(self, user):
        """Return CSS class for chat room pulse indicator if there are unseen messages"""
        room = self.chat_room
        if (room and room.messages.exists() and not room.seen_by.filter(id=user.id).exists()):
            return "chat-room-pulse"
        return ""


class TaskVote(models.Model):
    class Value(models.IntegerChoices):
        DOWN = -1, _("Against")
        UP = 1, _("For")

    task = models.ForeignKey(
        Task,
        related_name="votes",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        related_name="task_votes",
        on_delete=models.CASCADE,
    )
    value = models.IntegerField(choices=Value.choices)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("task", "user")

    def __str__(self):
        return f"{self.user} -> {self.task} ({self.get_value_display()})"


class TaskEvaluation(models.Model):
    class Value(models.TextChoices):
        SUCCESS = "success", _("Success")
        FAILURE = "failure", _("Failure")

    task = models.ForeignKey(
        Task,
        related_name="evaluations",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        related_name="task_evaluations",
        on_delete=models.CASCADE,
    )
    value = models.CharField(max_length=16, choices=Value.choices)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("task", "user")

    def __str__(self):
        return f"{self.user} -> {self.task} ({self.get_value_display()})"
