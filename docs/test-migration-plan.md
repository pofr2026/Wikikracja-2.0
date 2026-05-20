# Plan migracji testów z brancha `tests` do `ui`

> **Status: ZREALIZOWANY (2026-05-21)**
> Cel: cherry-pick wartościowych testów z brancha `tests` do `ui`, infrastruktura pytest + factory_boy, hybryda co-located/centralna
> Wynik: 24 nowe testy, wszystkie PASS; pełen suite 248/250 PASS (2 pre-existing flaky tests w `obywatele/tests/test_email.py` — nie regresja, race condition z thread + SQLite)

---

## Założenia (wykonane)

- ✅ **Struktura hybryda**: per-app testy zostają jak na `ui`; nowy `/tests/` w roocie dla cross-cutting
- ✅ **Pytest jako runner**: istniejące Django `TestCase` działają pod pytest natywnie
- ✅ **Cherry-pick** (NIE merge) — tylko wartościowe testy
- ✅ **Login flow przepisany** — `force_login` zamiast `client.login(username=...)` (allauth email-only)
- ✅ **Commit fazowo** — 6+1 commitów per faza

---

## Wykonane fazy

### ✅ Faza 0 — Środowisko
- `requirements.txt` + 4 paczki (pytest, pytest-django, pytest-asyncio, factory-boy)
- `pyproject.toml` — `[tool.pytest.ini_options]` z `zzz.test_settings`, `asyncio_mode=auto`, `asyncio_default_fixture_loop_scope=function`
- `tests/__init__.py`
- **Smoke test:** pytest zebrał 226 istniejących testów bez błędu

### ✅ Faza 1 — Fundamenty
- `tests/conftest.py` (7 fixtures, `force_login` + `UserFactory`)
- `tests/factories.py` (12 factories z `post_generation` password)
- `tests/test_smoke.py` (6 testów weryfikujących fundamenty)

### ✅ Faza 2 — WebSocket (8 testów)
`tests/test_websocket.py` — wszystkie 8 testów PASS w 11.5s.

### ✅ Faza 3 — Workflow (3 testy)
- `tests/test_workflow_glosowania.py` (2 testy, w tym test sygnału auto-tworzącego chat_room)
- `tests/test_workflow_chat.py` (1 test lifecycle wiadomości)

### ✅ Faza 4 — Performance (2 testy)
`tests/test_performance.py` — `CaptureQueriesContext` (NIE time-based) dla wykrycia N+1.

### ✅ Faza 5 — Per-app (5 testów)
- `bookkeeping/tests/__init__.py` + `test_models.py` (2 testy)
- `obywatele/tests/test_reputation.py` (3 testy Rate + reputation)
- ~~`chat/tests/test_models.py: test_duplicate_unique_field`~~ — **POMINIĘTE**: `chat/tests/test_models.py` ma już `test_unique_constraint_read_twice` dla MessageReadBy (linia 120-124). Dodanie `Room.title` unique testu byłoby duplikatem niskiej wartości.

### ✅ Faza 6 — Walidacja
- 24/24 nowych testów PASS
- 224/226 istniejących testów PASS
- 2 fail w `obywatele/tests/test_email.py` — **pre-existing flaky** (thread + SQLite race), nie nasza regresja, do osobnej naprawy

### ✅ Faza 7 — Commity (per faza) + dokumentacja

---

## Odkrycia (do project_architecture memory)

1. **`obywatele/models.py:82-86`** — sygnał `post_save(User)` auto-tworzy `Uzytkownik(uid=user)` przy każdym save User. NIE wolno ręcznie wywoływać `Uzytkownik.objects.create(uid=user)` — używaj `Uzytkownik.objects.get(uid=user)`.

2. **`glosowania/signals.py:16-49`** — sygnał `post_save(Decyzja)` przy `created=True and status=1` automatycznie tworzy chat_room z `public=True, protected=True, founder=author`, dodaje WSZYSTKICH aktywnych userów do `room.allowed`, tworzy welcome message. NIE wolno podawać `chat_room=` w `Decyzja.objects.create(...)` ani w factory — sygnał i tak nadpisze (utworzy orphan).

---

## Co świadomie POMIĘLIŚMY (z brancha `tests`)

| Plik | Powód |
|------|-------|
| `test_e2e.py` | Playwright + placebo asercje + login przez `[name="username"]` |
| `test_security.py` | **Aktywnie szkodliwe** — `# Accept 200 if view doesn't check` |
| `test_accessibility.py` | `or True` w każdej asercji |
| `test_admin.py` | Testy Django (nie aplikacji) |
| `test_api_integration.py` | Placebo + `assert True` |
| `test_migrations.py` | 5× `assert True` |
| `test_models_pytest.py` + 3 duplikaty + `test_create_models.py` | Tautologie ORM |
| `test_unit_tests.py` + `test_parametrized.py` | Tautologie + `is_archived` (nieistniejące pole) |
| `test_templates.py` | `or True` placebo |
| `test_validation.py` | `try/except assert True` placebo |
| `test_signals.py` | 1 sensowny test — TODO |
| `test_commands.py` | Testuje Django builtinów |
| `test_error_handling.py` | 1 sensowny test (`test_duplicate_unique_field`) — pominięty (duplikat) |
| `fixtures/*.json` (32 pliki) | Osobny audyt — TODO |
| `generate_fixtures.py` | Osobny review — TODO |

---

## TODO po migracji

1. **Naprawić 2 flaky testy email** w `obywatele/tests/test_email.py` (thread + SQLite race) — pre-existing
2. **Napisać prawdziwe security testy** — 3-4 z konkretnymi assertami zamiast wyrzuconego placebo
3. **Napisać testy custom management commands** — `chat_rooms`, `vote`, `count_citizens` (scheduler-critical)
4. **Audytować `fixtures/*.json`** z brancha `tests`
5. **Rozważyć playwright** dla real E2E
6. **Rozważyć sensowny chat unique test** jeśli pojawi się model bez constraintu — na razie pokrycie wystarczające

---

## Końcowe statystyki

| Metryka | Wartość |
|---------|---------|
| Nowych testów | 24 |
| Plików testowych nowych | 8 (`/tests/` × 6 + per-app × 2) |
| Plików testowych z brancha `tests` przyjętych | 0 (wszystkie przepisane od podstaw) |
| Plików testowych z brancha `tests` pominiętych | 21 |
| Łącznie testów w projekcie po migracji | 250 (224 stare + 24 nowe + 2 flaky) |
| Pełen pytest run | 248/250 PASS (~3 min) |
