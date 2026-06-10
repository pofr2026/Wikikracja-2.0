"""Tests for up/down voting on głosowania arguments.

The vote logic itself is covered by tests/test_reactions.py; here we pin
the HTTP contract of the AJAX endpoint and the permission rules that are
specific to arguments (blocked once a decision is closed).
"""
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from glosowania.models import Argument, Decyzja


class ArgumentVotingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username="alice", password="x")
        cls.bob = User.objects.create_user(username="bob", password="x")

    def _argument(self, status=2):
        d = Decyzja.objects.create(author=self.alice, title="t", tresc="x", status=status)
        return Argument.objects.create(
            decyzja=d, author=self.alice, argument_type="FOR", content="c"
        )

    def _url(self, argument):
        return reverse("glosowania:vote_argument", args=[argument.id])

    def _vote(self, argument, event="upvote"):
        return self.client.post(self._url(argument), {"event": event})

    # -- model --
    def test_reactions_default_empty(self):
        arg = self._argument()
        self.assertEqual(arg.reactions, {})

    # -- happy path --
    def test_upvote_casts_and_returns_counts(self):
        self.client.force_login(self.bob)
        arg = self._argument()
        resp = self._vote(arg, "upvote")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["upvotes"], 1)
        self.assertEqual(data["downvotes"], 0)
        self.assertTrue(data["active"])
        arg.refresh_from_db()
        self.assertEqual(arg.reactions["upvotes"], [self.bob.id])

    def test_second_identical_click_clears(self):
        self.client.force_login(self.bob)
        arg = self._argument()
        self._vote(arg, "upvote")
        resp = self._vote(arg, "upvote")
        data = json.loads(resp.content)
        self.assertEqual(data["upvotes"], 0)
        self.assertFalse(data["active"])

    def test_switching_side_moves_vote(self):
        self.client.force_login(self.bob)
        arg = self._argument()
        self._vote(arg, "upvote")
        resp = self._vote(arg, "downvote")
        data = json.loads(resp.content)
        self.assertEqual(data["upvotes"], 0)
        self.assertEqual(data["downvotes"], 1)
        self.assertTrue(data["active"])

    # -- permissions --
    def test_login_required(self):
        arg = self._argument()
        resp = self._vote(arg)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.url)

    def test_blocked_when_rejected(self):
        self.client.force_login(self.bob)
        arg = self._argument(status=4)
        resp = self._vote(arg)
        self.assertEqual(resp.status_code, 403)
        arg.refresh_from_db()
        self.assertEqual(arg.reactions, {})

    def test_blocked_when_approved(self):
        self.client.force_login(self.bob)
        arg = self._argument(status=5)
        resp = self._vote(arg)
        self.assertEqual(resp.status_code, 403)

    def test_bad_event_rejected(self):
        self.client.force_login(self.bob)
        arg = self._argument()
        resp = self.client.post(self._url(arg), {"event": "nonsense"})
        self.assertEqual(resp.status_code, 400)

    def test_get_not_allowed(self):
        self.client.force_login(self.bob)
        arg = self._argument()
        resp = self.client.get(self._url(arg))
        self.assertEqual(resp.status_code, 405)

    # -- details page renders the vote controls --
    def test_details_renders_vote_controls(self):
        self.client.force_login(self.bob)
        # status=1 so the post_save signal provisions the chat room the
        # details template's embedded chat expects.
        d = Decyzja.objects.create(author=self.alice, title="t", tresc="x", status=1)
        arg = Argument.objects.create(
            decyzja=d, author=self.alice, argument_type="FOR", content="c",
            reactions={"upvotes": [self.alice.id, self.bob.id], "downvotes": [1]},
        )
        resp = self.client.get(reverse("glosowania:details", args=[d.id]))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("arg-votes", html)
        self.assertIn(reverse("glosowania:vote_argument", args=[arg.id]), html)
        # 2 up / 3 total = 67% support bar visible
        self.assertIn("67% ", html)

    def test_details_hides_vote_buttons_when_closed(self):
        self.client.force_login(self.bob)
        # status=1 first so the signal provisions the chat room, then close it
        d = Decyzja.objects.create(author=self.alice, title="t", tresc="x", status=1)
        Decyzja.objects.filter(pk=d.pk).update(status=5)
        d.refresh_from_db()
        Argument.objects.create(
            decyzja=d, author=self.alice, argument_type="FOR", content="c",
            reactions={"upvotes": [self.alice.id]},
        )
        resp = self.client.get(reverse("glosowania:details", args=[d.id]))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        # closed decision: static counts, no clickable vote buttons
        self.assertIn("arg-vote-static", html)
        self.assertNotIn("arg-vote-btn", html)

    # -- argument sorting (reuses the glosowania querystring pattern) --
    def _decision_with_args(self):
        d = Decyzja.objects.create(author=self.alice, title="t", tresc="x", status=1)
        low = Argument.objects.create(
            decyzja=d, author=self.alice, argument_type="FOR", content="low",
            reactions={},
        )
        high = Argument.objects.create(
            decyzja=d, author=self.alice, argument_type="FOR", content="high",
            reactions={"upvotes": [self.alice.id, self.bob.id], "downvotes": []},
        )
        return d, low, high

    def test_sort_by_likes_desc(self):
        self.client.force_login(self.bob)
        d, low, high = self._decision_with_args()
        resp = self.client.get(
            reverse("glosowania:details", args=[d.id]) + "?sort=likes&order=desc"
        )
        pos = resp.context["positive_arguments"]
        self.assertEqual([a.id for a in pos], [high.id, low.id])

    def test_filter_popular_hides_unvoted(self):
        self.client.force_login(self.bob)
        d, low, high = self._decision_with_args()
        resp = self.client.get(
            reverse("glosowania:details", args=[d.id]) + "?filter=popular"
        )
        pos = resp.context["positive_arguments"]
        self.assertEqual([a.id for a in pos], [high.id])

    def test_default_sort_is_date(self):
        self.client.force_login(self.bob)
        d, low, high = self._decision_with_args()
        resp = self.client.get(reverse("glosowania:details", args=[d.id]))
        self.assertEqual(resp.context["arg_sort"], "date")
