from django.db.models import Count, Exists, OuterRef, Q

from glosowania.models import Decyzja, ZebranePodpisy


def get_stepper_counts():
    """Return counts per stepper stage in a single aggregate query.

    discussion/referendum count only items whose author has signed
    (same filter as is_author_signed in the views).
    """
    # Orphaned decyzjas (author=NULL after user deletion) are excluded:
    # SQL NULL comparison in Exists is falsy, matching Decyzja.is_author_signed.
    author_signed = Exists(
        ZebranePodpisy.objects.filter(
            projekt=OuterRef("pk"),
            podpis_uzytkownika_id=OuterRef("author_id"),
        )
    )
    return Decyzja.objects.annotate(_signed=author_signed).aggregate(
        proposition=Count("id", filter=Q(status=1)),
        discussion=Count("id", filter=Q(status=2, _signed=True)),
        referendum=Count("id", filter=Q(status=3, _signed=True)),
        rejected=Count("id", filter=Q(status=4)),
        approved=Count("id", filter=Q(status=5)),
    )
