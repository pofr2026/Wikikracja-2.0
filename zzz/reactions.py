"""Reusable up/down vote core over a `reactions` JSONField.

Shared between chat messages and głosowania arguments so the voting
behaviour — and the JSON shape it produces — stays identical across the
whole app instead of being reimplemented per feature.

The functions are pure: they take a plain dict (the value of a model's
`reactions` JSONField), mutate and return it, and do no DB I/O. Callers
are responsible for persisting the returned dict.

JSON shape: ``{"upvotes": [user_id, ...], "downvotes": [user_id, ...]}``.
A user holds at most one of the two.
"""

UPVOTES = "upvotes"
DOWNVOTES = "downvotes"

# Support-bar presentation thresholds. The chat EJS template
# (chat/static/chat/js/templates.js) mirrors these numbers in JS — keep the
# two in sync; this is the canonical definition.
VOTE_BAR_MIN_VOTES = 3
VOTE_BAR_POSITIVE_PCT = 60
VOTE_BAR_NEUTRAL_PCT = 40


def normalize(reactions):
    """Return a usable dict even if the field was None or some other type.

    JSONField defaults and legacy rows can leave the value as None; every
    helper funnels through here so callers never have to guard for it.
    """
    return reactions if isinstance(reactions, dict) else {}


def _target(event):
    return UPVOTES if event == "upvote" else DOWNVOTES


def set_vote(reactions, user_id, event):
    """Cast (or re-cast) a single user's vote and return the dict.

    Enforces one vote per user: any existing up/down vote by this user is
    dropped first, then the requested one is recorded. Re-casting the vote
    the user already holds is a no-op on the counts (removed then re-added).
    """
    reactions = normalize(reactions)
    reactions.setdefault(UPVOTES, [])
    reactions.setdefault(DOWNVOTES, [])

    if user_id in reactions[UPVOTES]:
        reactions[UPVOTES].remove(user_id)
    if user_id in reactions[DOWNVOTES]:
        reactions[DOWNVOTES].remove(user_id)

    reactions[_target(event)].append(user_id)
    return reactions


def clear_vote(reactions, user_id, event):
    """Remove the user's vote of the given kind if present; else no-op."""
    reactions = normalize(reactions)
    target = _target(event)
    if user_id in reactions.get(target, []):
        reactions[target].remove(user_id)
    return reactions


def toggle_vote(reactions, user_id, event):
    """Single UI entry point: a click toggles the given vote.

    If the user already holds exactly this vote, it is cleared; otherwise
    it is cast (switching sides if they held the opposite one). Returns
    ``(reactions, active)`` where ``active`` is True when the vote is now
    set and False when it was just cleared.
    """
    if user_vote(reactions, user_id) == event:
        return clear_vote(reactions, user_id, event), False
    return set_vote(reactions, user_id, event), True


def vote_counts(reactions):
    """Return ``(upvote_count, downvote_count)``."""
    reactions = normalize(reactions)
    return len(reactions.get(UPVOTES, [])), len(reactions.get(DOWNVOTES, []))


def vote_bar(reactions):
    """Presentation data for the support bar, derived from the vote counts.

    Returns a dict with the up/down counts, total, support percentage,
    the CSS modifier class for the fill colour, and whether the bar should
    be shown at all (only once enough votes have accumulated).
    """
    up, down = vote_counts(reactions)
    total = up + down
    pct = round(up / total * 100) if total else 0
    if pct >= VOTE_BAR_POSITIVE_PCT:
        css = "vote-bar--positive"
    elif pct >= VOTE_BAR_NEUTRAL_PCT:
        css = "vote-bar--neutral"
    else:
        css = "vote-bar--negative"
    return {
        "up": up,
        "down": down,
        "total": total,
        "pct": pct,
        "css": css,
        "show": total >= VOTE_BAR_MIN_VOTES,
    }


def user_vote(reactions, user_id):
    """Return ``'upvote'`` / ``'downvote'`` / ``None`` for the given user."""
    reactions = normalize(reactions)
    if user_id in reactions.get(UPVOTES, []):
        return "upvote"
    if user_id in reactions.get(DOWNVOTES, []):
        return "downvote"
    return None
