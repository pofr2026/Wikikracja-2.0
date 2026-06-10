"""Unit tests for the reusable up/down vote core (`zzz.reactions`).

Pure-function tests: no DB, no async. They pin down the exact behaviour
that chat messages rely on today, so the same core can back głosowania
arguments without the two drifting apart.
"""
from zzz import reactions as r


class TestNormalize:
    def test_none_becomes_empty_dict(self):
        assert r.normalize(None) == {}

    def test_non_dict_becomes_empty_dict(self):
        assert r.normalize("nope") == {}

    def test_dict_passes_through(self):
        d = {"upvotes": [1]}
        assert r.normalize(d) is d


class TestSetVote:
    def test_upvote_on_empty(self):
        assert r.set_vote({}, user_id=1, event="upvote") == {
            "upvotes": [1],
            "downvotes": [],
        }

    def test_downvote_on_empty(self):
        assert r.set_vote({}, user_id=1, event="downvote") == {
            "upvotes": [],
            "downvotes": [1],
        }

    def test_switching_side_moves_the_vote(self):
        d = r.set_vote({}, user_id=1, event="upvote")
        d = r.set_vote(d, user_id=1, event="downvote")
        assert d == {"upvotes": [], "downvotes": [1]}

    def test_recasting_same_side_does_not_duplicate(self):
        d = r.set_vote({}, user_id=1, event="upvote")
        d = r.set_vote(d, user_id=1, event="upvote")
        assert d == {"upvotes": [1], "downvotes": []}

    def test_independent_users_accumulate(self):
        d = r.set_vote({}, user_id=1, event="upvote")
        d = r.set_vote(d, user_id=2, event="upvote")
        assert d["upvotes"] == [1, 2]

    def test_handles_none_field(self):
        assert r.set_vote(None, user_id=1, event="upvote") == {
            "upvotes": [1],
            "downvotes": [],
        }


class TestClearVote:
    def test_removes_existing_upvote(self):
        d = {"upvotes": [1, 2], "downvotes": []}
        assert r.clear_vote(d, user_id=1, event="upvote") == {
            "upvotes": [2],
            "downvotes": [],
        }

    def test_noop_when_vote_absent(self):
        d = {"upvotes": [2], "downvotes": []}
        assert r.clear_vote(d, user_id=1, event="upvote") == {
            "upvotes": [2],
            "downvotes": [],
        }

    def test_wrong_kind_is_noop(self):
        # user holds an upvote; clearing their (non-existent) downvote leaves it
        d = {"upvotes": [1], "downvotes": []}
        assert r.clear_vote(d, user_id=1, event="downvote") == {
            "upvotes": [1],
            "downvotes": [],
        }

    def test_handles_none_field(self):
        assert r.clear_vote(None, user_id=1, event="upvote") == {}


class TestToggleVote:
    """toggle_vote = the single entry point the UI needs: a click either
    casts the vote or, if the user already holds that exact vote, clears it."""

    def test_first_click_casts(self):
        d, active = r.toggle_vote({}, user_id=1, event="upvote")
        assert active is True
        assert d == {"upvotes": [1], "downvotes": []}

    def test_second_identical_click_clears(self):
        d, _ = r.toggle_vote({}, user_id=1, event="upvote")
        d, active = r.toggle_vote(d, user_id=1, event="upvote")
        assert active is False
        assert d == {"upvotes": [], "downvotes": []}

    def test_clicking_opposite_switches(self):
        d, _ = r.toggle_vote({}, user_id=1, event="upvote")
        d, active = r.toggle_vote(d, user_id=1, event="downvote")
        assert active is True
        assert d == {"upvotes": [], "downvotes": [1]}


class TestCounts:
    def test_vote_counts(self):
        d = {"upvotes": [1, 2, 3], "downvotes": [4]}
        assert r.vote_counts(d) == (3, 1)

    def test_vote_counts_on_none(self):
        assert r.vote_counts(None) == (0, 0)


class TestVoteBar:
    """Canonical spec for the support bar (chat's EJS template mirrors these
    numbers): bar shows from 3 total votes, colour by support percentage."""

    def test_hidden_below_threshold(self):
        bar = r.vote_bar({"upvotes": [1, 2], "downvotes": []})
        assert bar["show"] is False
        assert bar["total"] == 2

    def test_shown_at_threshold(self):
        bar = r.vote_bar({"upvotes": [1, 2], "downvotes": [3]})
        assert bar["show"] is True
        assert bar["pct"] == 67  # 2/3

    def test_positive_band(self):
        bar = r.vote_bar({"upvotes": [1, 2, 3], "downvotes": []})
        assert bar["pct"] == 100
        assert bar["css"] == "vote-bar--positive"

    def test_neutral_band(self):
        # 2 up / 3 total = 40% -> neutral
        bar = r.vote_bar({"upvotes": [1, 2], "downvotes": [3, 4, 5]})
        assert bar["pct"] == 40
        assert bar["css"] == "vote-bar--neutral"

    def test_negative_band(self):
        bar = r.vote_bar({"upvotes": [1], "downvotes": [2, 3, 4]})
        assert bar["pct"] == 25
        assert bar["css"] == "vote-bar--negative"

    def test_empty(self):
        bar = r.vote_bar(None)
        assert bar == {
            "up": 0, "down": 0, "total": 0,
            "pct": 0, "css": "vote-bar--negative", "show": False,
        }


class TestUserVote:
    def test_returns_upvote(self):
        assert r.user_vote({"upvotes": [1]}, user_id=1) == "upvote"

    def test_returns_downvote(self):
        assert r.user_vote({"downvotes": [1]}, user_id=1) == "downvote"

    def test_returns_none_when_no_vote(self):
        assert r.user_vote({"upvotes": [2]}, user_id=1) is None

    def test_returns_none_on_empty(self):
        assert r.user_vote(None, user_id=1) is None
