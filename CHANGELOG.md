# CHANGELOG


## v1.3.2 (2026-05-19)

### Bug Fixes

- **scheduler**: Konwertuj czas spotkania na lokalna strefe czasowa w powiadomieniach
  ([`9e21fdf`](https://github.com/soma115/Wikikracja/commit/9e21fdf6064ffaee97f069ef389fefdb2fd0b41c))


## v1.3.1 (2026-05-09)

### Bug Fixes

- **settings**: Read version from pyproject.toml instead of installed package metadata
  ([`475afca`](https://github.com/soma115/Wikikracja/commit/475afcae3e925f7c1c82b26ea502128b3e1ae10e))


## v1.3.0 (2026-05-09)

### Bug Fixes

- Build/merge duplicate translations
  ([`cead3ed`](https://github.com/soma115/Wikikracja/commit/cead3ed05f4b0db1f722966b1adcde3e54082275))

- **chat**: Declare glosowania dependency in 0017_room_founder migration
  ([`33af2af`](https://github.com/soma115/Wikikracja/commit/33af2af2d688b6c4d96ced85cf6b43b37f0fb95e))

What was broken --------------- The data migration chat/0017_room_founder.py calls Decyzja =
  apps.get_model('glosowania', 'Decyzja') to backfill the `founder` field for referendum chat rooms
  — but its `dependencies` list only mentioned chat/0016 and the User model. It never declared the
  glosowania app.

Why that's a bug ---------------- Django decides migration ordering ONLY from the explicit
  `dependencies` list — it does not infer dependencies from code inside RunPython functions. Without
  the declaration, Django was free to plan chat/0017 before any glosowania migration had run. On a
  fresh database (tests, CI, fresh clone) the Decyzja model didn't exist yet at that point, so
  apps.get_model('glosowania', 'Decyzja') raised: LookupError: No installed app with label
  'glosowania'.

This never surfaced on existing databases because chat/0017 was already recorded in
  django_migrations there — Django skips it on subsequent runs and the buggy code path simply never
  executes again.

Fix --- Add ('glosowania', '0013_auto_20260408_1446') to the dependencies. That's the migration that
  introduces Decyzja.chat_room, which is the exact field the data migration queries. Now Django
  guarantees the glosowania schema exists before chat/0017 runs.

Safety ------ Zero risk for already-migrated databases: Django respects dependencies only when
  planning what to run next, not when re-checking what is already applied. Production and dev DBs
  continue as-is; only fresh test/CI builds change behavior — they now succeed instead of crashing.

- **chat**: Eliminate duplicate sends and unblock broadcast on push notifications
  ([`165f4c4`](https://github.com/soma115/Wikikracja/commit/165f4c4fd0b2898c058c5ba4af3be629046ebf8c))

- asyncio.create_task() for push notifications in consumers.py so they no longer block the
  group_send broadcast (was causing 1-3s delay) - Disable send button immediately on submit,
  re-enable when own message returns via broadcast; 5s timeout as safety net (chat.js) - Same lock
  pattern in embedded chat (chat-embedded.js)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>

- **chat**: Expandable hint — inline bottom-right, horizontal gradient
  ([`78f1bfe`](https://github.com/soma115/Wikikracja/commit/78f1bfe6ab7399bfacc032822ab22c3110afc081))

Replace full-width vertical overlay with bottom-right inline hint that sits on the last visible line
  (Facebook-style). Layered horizontal gradients ensure solid background even when --expandable-bg
  is semi-transparent (own messages use rgba accent-muted).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **chat**: Open_dm creates DM room on demand
  ([`406ab96`](https://github.com/soma115/Wikikracja/commit/406ab962037f3b6f50ebb8d85d98cea20933d9a6))

Clicking the chat icon for a citizen on /obywatele/ used to silently redirect to the chat list when
  no 1:1 room existed yet — relying solely on the user_accepted signal to materialize all pairs.
  open_dm now creates the missing room on the fly, reactivates archived ones, and always redirects
  with #room_id so the chat page opens the conversation.

- **events**: Calendar dots respect start_date; prevent chunk overlap in grid
  ([`9caf588`](https://github.com/soma115/Wikikracja/commit/9caf588d9e19455b37d67d1f700d470baf1944f6))

- build_calendar_grid: daily/weekly events now respect start_date — calendar no longer shows dots on
  days before the event begins - jumpToDay: check loadedMonths before fetching a chunk to avoid
  re-loading months already in the initial 90-day window (prevented doubled cards in grid view) -
  Remove scrollToFirstVisible — display:none hides past content so no scroll is needed; native
  anchor scroll caused off-by-one in viewport

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **home**: Show 5 upcoming events instead of 3 on dashboard
  ([`0c859c9`](https://github.com/soma115/Wikikracja/commit/0c859c97106dd2e744122457dd7fe42a04f63b4e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tasks**: Capture-phase click listener prevents card collapse on vote
  ([`0d147fd`](https://github.com/soma115/Wikikracja/commit/0d147fdaf60a66dbbf834e412327d142f06d144f))

Replace submit-event delegation with capture-phase click listener
  (document.addEventListener('click', handler, true)) so the handler fires before card-body onclick
  (navigate to detail) and card-header onclick (toggleCard) can execute. Also remove form.submit()
  fallback in catch to avoid page reloads on AJAX errors.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Chores

- **i18n**: Sync django.po z upstream (POT-Creation-Date + numery linii)
  ([`fd16753`](https://github.com/soma115/Wikikracja/commit/fd167530c253d8d887a98bd02cd19c0f255ce8aa))

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>

### Features

- **categories**: Shared category system for board, tasks & elibrary
  ([`2fe94cd`](https://github.com/soma115/Wikikracja/commit/2fe94cd2404caf19828615c0ef289b2a09ca624c))

- New `categories` app: AbstractCategory base model + generic API views (CategoryAPIBase,
  CategoryEditAPI, CategoryDeleteAPI, CategoryReorderAPI) - board: PostCategory inherits
  AbstractCategory, category filter dropdown, manage modal with drag-and-drop reorder, cache
  invalidation for elibrary - tasks: Category refactored onto shared base, reorder API added -
  elibrary: category filter + manage modal reusing board categories - SortableJS (local, v1.15.6)
  for DnD reorder; shared JS modules (category-manager.js, sortable-list.js) loaded globally from
  base.html - Global design: inline styles extracted to CSS utility classes (.post-row-link,
  .post-card-link, .cat-group-icon, .text-*-clamp, .avatar-*, .book-*, .text-meta, .text-author);
  board/elibrary templates unified to card/card-header/card-body structure - Removed stale
  postcategory_list/form/confirm_delete templates - Polish translations updated for all new UI
  strings

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>

- **chat**: Expandable long messages, raise message limit to 1000, project docs
  ([`ec28ec0`](https://github.com/soma115/Wikikracja/commit/ec28ec0f24552f284693dd49aea935443f4f17ab))

- Long chat messages are clipped at ~9 lines with "… pokaż więcej" hint; click anywhere to toggle
  expand/collapse. markOverflow() detects when content actually overflows so short messages don't
  show the hint. Note: hint overlay still has stacking issue — needs refinement (see TODO). - Raise
  MESSAGE_MAX_LENGTH default from 500 to 1000 and surface it on /site-settings/. - Expose redis port
  in docker-compose for local Django access. - Add CLAUDE.md with project working rules and design
  system guide.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **chat**: Live unread counter — Redis cache + WebSocket push + routing do pierwszej
  nieprzeczytanej
  ([`de7be32`](https://github.com/soma115/Wikikracja/commit/de7be32f3942e3840f50c14c8ca69c719d17340b))

## Co zostało zmienione

### Backend - **chat/services.py**: Redis cache dla licznika nieprzeczytanych pokoi per-user (klucz
  `chat_unread:{user_id}`, TTL 5 min). Invalidacja przy `see_room` / `unsee_room`. Nowa metoda
  `ChatRepository.get_unread_count()`. - **chat/consumers.py**: Każdy user dołącza do grupy
  `user_{id}` przy WS connect. Po `room-seen` / `room-unseen` serwer pushuje zaktualizowany licznik
  przez `{type: "chat.unread_count", count: N}` do tej grupy. Nowe metody: `push_unread_count()` i
  handler `chat_unread_count(event)`. Przy WS connect serwer od razu wysyła bieżący licznik do
  klienta. - **home/views.py**: `chat_unread_count` czytany z cache Redis, obliczany z DB tylko przy
  cache miss. - **chat/views.py**: Nowy endpoint `GET /chat/api/unread-count/` → `{"count": N}` (z
  cache, bez uderzania w DB przy każdym żądaniu). - **chat/urls.py**: Rejestracja nowego URL
  `api/unread-count/`.

### Frontend - **home/templates/home/home.html**: Badge czatu ma `id="chat-unread-badge"`. Link
  prowadzi do `/chat/?unread=1` gdy są nieprzeczytane pokoje. Dodany JS: (a) `visibilitychange` —
  odświeża licznik gdy użytkownik wraca do zakładki (fix bfcache / back-navigation), (b) lekkie
  połączenie WS `/chat/stream/` — gdy serwer pushnie `unread_count`, badge aktualizuje się
  natychmiast bez przeładowania strony. - **chat/static/chat/js/chat.js**: Przy starcie czatu z
  `?unread=1` aktywowany jest filtr "Nieprzeczytane" i otwierany pierwszy nieprzeczytany pokój. URL
  param czyszczony przez `history.replaceState`.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>

- **chat/mobile**: Sticky toolbar, brak autofocusu, lista pokoi przy ?unread=1
  ([`1b3d610`](https://github.com/soma115/Wikikracja/commit/1b3d610b130d195a4f4c69a0b8be99d4f0616483))

- CSS: .room-list-controls sticky top:0 na mobile — toolbar z przyciskami (+ Pokój, Nieprzeczytane,
  itp.) zostaje przyklejony u góry panelu listy pokoi nawet gdy użytkownik scrolluje w dół przez
  długą listę - JS: messageInput.focus() przy wejściu do pokoju tylko na desktop (>= 768px) — na
  mobile klawiatura nie otwiera się automatycznie, dopiero po kliknięciu w pole wpisywania - JS:
  ?unread=1 z pulpitu — na desktop otwiera pierwszy nieprzeczytany pokój, na mobile zostaje na
  liście pokoi z aktywnym filtrem "Nieprzeczytane" żeby użytkownik sam wybrał pokój

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>

- **events**: Agenda/grid views with mini-calendar drawer and lazy chunk loading
  ([`f68314c`](https://github.com/soma115/Wikikracja/commit/f68314c1ab1e46e4614f3e96ccd08d722f2c9f95))

- New agenda list view: month/day grouping, event chips, past days hidden by default - Grid view:
  expandable cards (pk+date IDs to avoid collisions across chunks) - Single toolbar drawer trigger
  for mini-calendar; closes on outside click or day double-click - Day click filters both agenda and
  grid from selected date; stays in current view - Lazy 3-month chunk loading when clicking a
  far-future day not yet in DOM - New views: events_agenda_chunk (AJAX partial), events_calendar
  reused for drawer - build_calendar_grid extracted to events/calendar.py, shared with obywatele -
  Polish month names via Django i18n date filter (cal_first_day|date:"F Y") - Grid defaults to
  hiding past cards on initial load (consistent with agenda)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **glosowania**: Increase law text max length from 1000 to 2000 chars
  ([`003a900`](https://github.com/soma115/Wikikracja/commit/003a90028197173e1926f54904f486ab2d6ac219))

- **home**: Make New Citizens card fully clickable
  ([`863d895`](https://github.com/soma115/Wikikracja/commit/863d895db1b251f247eb84f11c5222377d521366))

Whole card links to citizen list via Bootstrap stretched-link. Individual citizen avatars and
  waiting-badge link keep their own targets via position:relative (above the stretched-link in
  stacking context).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tasks**: Ajax voting, global design buttons, tooltips
  ([`d487a52`](https://github.com/soma115/Wikikracja/commit/d487a5285390035a670fecd7b271194f8fd822e8))

- vote_task view returns JSON for AJAX requests (X-Requested-With header) tracking new_vote value
  and votes_up count - new tasks/static/tasks/js/tasks.js: single shared handleVoteSubmit function
  used by both list and detail views — no code duplication; updates button state (active-vote, icon,
  text) and vote counters in-place without page reload or closing expanded card - task_detail.html +
  _task_card.html: replaced generic Bootstrap btn-* classes with project design-system classes
  (task-vote-btn, action-btn, task-take-btn, task-resign-btn) that use CSS variables and adapt to
  all themes; added data-text/icon/tooltip-active/inactive attributes - Bootstrap tooltips on all
  action buttons with context-sensitive text - i18n: 8 new Polish translations for button states and
  tooltips

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tasks**: Coordinator role + helpers popover on task cards
  ([`a523258`](https://github.com/soma115/Wikikracja/commit/a523258ac5ba6b725cbc3a32786c2957bec8d4f9))

- meta strip: Autor → Koordynator · Data · ❤ N · Detale with role icons (fa-user-pen, fa-user-gear,
  fa-clock-rotate-left) - per-element tooltips (author, coordinator, date, helpers count, details) -
  lazy-loaded helpers popover (hover on desktop, click on touch devices) via new
  tasks/<pk>/helpers.json endpoint, up to 10 avatars + "and N more" - DOMPurify sanitization for
  popover html; cache invalidated on vote change - rename UI: "Take task"/"Resign" →
  "Zostań/Zrezygnuj z koordynacji", "Owner"/"Assigned to" → "Koordynator" across card and detail
  views - refactor inline styles in body to .task-assignee-link/.task-assignee-empty - new pl
  translations for all introduced strings

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>

- **tasks**: Dynamic categories — DB model, CRUD API, manage modal
  ([`186e3be`](https://github.com/soma115/Wikikracja/commit/186e3be58c0006003814c5dfb5dd481990f93f06))

Replaces hardcoded Task.Category TextChoices with a proper Category model (slug, name, description,
  order, is_protected). Users can now add, edit and delete categories from the task list UI via a
  modal opened from the category filter panel.

- Migration 0008: creates tasks_category table, seeds 7 existing categories, migrates Task.category
  varchar→FK (SET_NULL on delete) - API endpoints: GET/POST /api/categories/, POST
  /api/categories/<pk>/edit|delete/ - Modal: inline edit, add new, delete with affected-task count
  warning - Category filter reads slugs from DB instead of TextChoices - CSS via design tokens (no
  hardcoded colours); theme-aware

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **ui**: Persistent filters and view settings via PagePrefs
  ([`4ac97b0`](https://github.com/soma115/Wikikracja/commit/4ac97b04cd3381ec04151209bee4c508c9488c8a))

Replaces 5 separate localStorage wrappers (setTaskView, setProposalsView, setElibraryView,
  setBoardView, setActivityView) with a single global PagePrefs module. Filters (URL params),
  grid/list toggle and Bootstrap tab selection are now stored per-scope in one JSON key
  (wikikracja:prefs:{scope}) and restored on return visit without flashing.

- Anti-FOUC head-script restores URL filters before body renders - Patches history.pushState to
  capture JS-driven URL changes (category filter) - HTML uses data-view / data-view-container
  conventions — zero onclick bindings - Elibrary category filter gains URL sync (was DOM-only, now
  shareable) - One-shot migration of legacy localStorage keys on first load

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **tasks**: Add test_settings.py to run tests without Redis
  ([`395cea4`](https://github.com/soma115/Wikikracja/commit/395cea4cd820bc2444314bf3b21e011d24af00c2))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v1.2.0 (2026-05-01)

### Bug Fixes

- **chat**: Fix image upload button, size limit, and lightbox in embedded chat
  ([`7f45ced`](https://github.com/soma115/Wikikracja/commit/7f45ceda1126593678d73a50e11315247979e56f))

- Fix image upload button not opening file dialog: fmt-btn click handler was calling
  e.preventDefault() unconditionally, blocking the label's default action — now only fires for
  buttons with data-cmd - Fix upload field name in chat-core.js: was 'files', server expects
  'images' - Fix upload size limit: remove accidental *2 multiplier in views.py, align JS client
  (wsapi.js, chat-core.js) to match UPLOAD_IMAGE_MAX_SIZE_MB=5 - Unify lightbox: extract
  openBigImage + createImageClickHandler into chat-core.js as shared exports; domapi.js delegates,
  chat-embedded.js now uses the same lightbox as main chat

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **chat**: Unify formatting toolbar — fix active state and focus-theft bug
  ([`bc662a6`](https://github.com/soma115/Wikikracja/commit/bc662a60efe945256f622a054c3469578b98ed8c))

- Anonymous button now uses same active style as B/I/U (removed custom .anonymous-toggle.active CSS
  override) - Extracted initFormattingToolbar() to chat-core.js — single definition used by both
  main chat and embedded chat - mousedown preventDefault prevents focus-theft, so text selection is
  preserved when clicking toolbar buttons; fixes "deselect one resets all" - Fixed
  updateToolbarState in embedded chat scoping to [data-cmd] only, so anonymous button active state
  is no longer reset on selectionchange - Removed dead const-reassignment block in handlers.js
  (would crash in strict/module mode when SITE_SETTINGS.messageMaxLength is set) - Fixed
  content.classList.remove('open') accidentally inside comment

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **chat**: Compress uploads to WebP and lazy-load attached images
  ([`87c177a`](https://github.com/soma115/Wikikracja/commit/87c177a4d9f83a99598a856f84a1acc75292b823))

- On upload: resize to max 1920px long side (LANCZOS), convert to WebP @85% quality — typically
  3-10x smaller than original PNG/JPEG - Use image.size for size check instead of reading full bytes
  to memory - Add loading="lazy" to attached-image elements so browser defers off-screen images
  instead of loading entire chat history at once

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- **chat**: Unify upload size limit into single UPLOAD_MAX_BYTES constant
  ([`b343c12`](https://github.com/soma115/Wikikracja/commit/b343c1295d2d03ad9fc6022d1faed0f3a39ebe01))

Move hardcoded 5MB limit from wsapi.js and chat-core.js into one exported constant in chat-core.js,
  imported by wsapi.js — single source of truth.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v1.1.0 (2026-04-29)

### Bug Fixes

- Add reaction counts for messages in chat
  ([`3486f63`](https://github.com/soma115/Wikikracja/commit/3486f63aebd084c80b7026d087b9beeea98a69cb))

- Badly merged user chats view
  ([`a1f8144`](https://github.com/soma115/Wikikracja/commit/a1f8144ba79d1af4c3a67da6724f6409e15ae34e))

- Bug: chat activity does not list the real messages of the person selected
  ([`c1022dc`](https://github.com/soma115/Wikikracja/commit/c1022dcae03721baa1487d1b9160a47b172c8b48))

- Chat reactions does not work on first click on them
  ([`e107843`](https://github.com/soma115/Wikikracja/commit/e107843fd5c137d86f2324e48462fbe891c8cb53))

- Migrations and settings
  ([`3b448e8`](https://github.com/soma115/Wikikracja/commit/3b448e8f8de6cf594dbbe3cffbbcf49e671f5ea3))

- Semantic build, unneded json
  ([`711a20b`](https://github.com/soma115/Wikikracja/commit/711a20b449116aa3250da0c2719a35081697ff7f))

- Set created_at on in-memory task objects in test helpers
  ([`f41d8cf`](https://github.com/soma115/Wikikracja/commit/f41d8cf2fa8c32dbf2f95ce2bfe1cf594816b4e4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **chat**: Fix compose bar overflow on narrow mobile screens
  ([`20f3a54`](https://github.com/soma115/Wikikracja/commit/20f3a54506eee79ddaf23d82f84789d260937a85))

- Reduce padding in embedded chat on mobile (ec-messages, ec-input-area, compose-bar) to gain ~30px
  horizontal space - Add flex-wrap to compose-bar on mobile so send button wraps to a second line
  instead of overflowing — applies to both main and embedded chat - Remove dead CSS: unused
  .chat-controls-row and redundant .send-message display override

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **chat**: Fix reply-to button not working — missing import of setReplyTarget
  ([`ef3837f`](https://github.com/soma115/Wikikracja/commit/ef3837f24b236fa6f07d0c57124bb084cd304da2))

Clicking the reply button caused a ReferenceError because setReplyTarget was used in handlers.js but
  never imported from chat.js. As a result, currentReplyId was never set and messages were sent
  without reply_to_id, so quoted/reply messages were silently broken.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **chat**: Make quote-jump return button work in embedded chat
  ([`dca7b16`](https://github.com/soma115/Wikikracja/commit/dca7b166b249a7676f26b0bbf369adb92fee6c49))

Move showReturnBtn logic into createQuoteJumpHandler in chat-core.js so it is shared by both main
  and embedded chat views. Remove ~60 lines of duplicate handler code from handlers.js.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **chat**: Scroll listy pokojów, batch rendering, reconnect fix
  ([`09c3726`](https://github.com/soma115/Wikikracja/commit/09c3726875ad139aa21d2df276c7875e81c47d02))

- CSS: 100dvh, layout-wrapper/main-area height chain, room-list height:0 flex:1 1 0 - CSS:
  room-list-controls flex-shrink:0 (zamiast sticky), mobile safe-area-inset - JS: batch rendering
  wiadomości przy join (jeden insertAdjacentHTML zamiast N) - JS: reconnect guard — reset
  CurrentRoomId przed rejoinem po reconnect WebSocket - JS: parseInt(room_id) i strict === w
  onRoomTryJoin i onReceiveMessages - domapi.js: buildMessageHtml jako osobna metoda dla batch
  renderingu

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **chat**: Strip HTML tags from email notifications
  ([`b747b1b`](https://github.com/soma115/Wikikracja/commit/b747b1b191e60c6e5f37f6098b2d35647064720a))

<br> tags converted to newlines, other HTML tags removed before inserting message text into
  plain-text email body.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **editor**: Improve TinyMCE layout and usability globally
  ([`2750c7e`](https://github.com/soma115/Wikikracja/commit/2750c7e250d97b8f6f84e81aea93fc6140ec1b9a))

- elibrary book_form: widen editor column (col-md-6 → col-md-8), narrow uploads sidebar (col-md-4) -
  uploader.js: sliding toolbar mode, fixed height 500px, manual resize handle, remove autoresize
  plugin - app.css: ensure .tox-tinymce fills container width on all screen sizes

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **richtext**: Zastosuj |richtext również w podglądach kart i potwierdzeniu usunięcia
  ([`b1542c2`](https://github.com/soma115/Wikikracja/commit/b1542c2cc157ac5cf2b0c9bfa45b6231fb13bec3))

W poprzednim commicie objąłem widok szczegółów (rozwinięty kafelek), ale przegapiłem kilka miejsc
  gdzie pola opisu są renderowane raw:

- tasks/_task_card.html:53 (Agora-style preview na liście /tasks/) — widoczny był surowy <b>...</b>
  w tekście podglądu pod tytułem zadania. - glosowania/_proposal_card.html:60 (preview na liście
  propozycji, /glosowania/proposition/) — analogiczny problem dla pola tresc. -
  events/event_confirm_delete.html:18 (potwierdzenie usunięcia wydarzenia) — |truncatewords:30
  zostawiało raw HTML. - home/search.html:141 (wyniki wyszukiwania, mieszane typy contentu) — raw {{
  item.description }} jednolinijkowo z white-space:nowrap. Tu użyty |striptags zamiast |richtext, bo
  description w wynikach pochodzi z różnych modeli (task/post/book/event/...) i niektóre mają
  TinyMCE HTML — strip do plain tekstu daje spójny preview niezależnie od źródła.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>

### Chores

- Merge remote ui branch, resolve locale conflicts
  ([`67ab606`](https://github.com/soma115/Wikikracja/commit/67ab6067edee4f341e6a5f23ff67ef22199a71d1))

Accept remote line-number references in django.po (11 upstream commits updated obywatele/views.py
  line numbers); accept deletion of en locale.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **chat**: Add Room.founder field with backfill migration; fix citizen activity tabs
  ([`72c1dc1`](https://github.com/soma115/Wikikracja/commit/72c1dc1eac2406ccf0ccb5393d6c340d5916201a))

- Add `founder` ForeignKey to Room model (null=True for legacy rooms) - Migration 0017 backfills
  founder: referendum rooms via Decyzja.author, task rooms and manual rooms via first message sender
  - Set founder on Room creation in glosowania and tasks signals - citizen_czaty: show messages sent
  by the user instead of rooms they belong to - citizen_zalozono: include rooms founded by the user

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **chat**: Mobile room-list toggle, unified sort-btn styles, layout fixes
  ([`d349361`](https://github.com/soma115/Wikikracja/commit/d3493610ff00351e14e1e4ef5620b979f18d82a2))

Mobile: - Replace folded-room-header/drawer with room-active + room-list-showing CSS classes - Sort
  toolbar << shows room list without leaving room; >> next to Unread returns to chat - Send button
  always visible on mobile

Desktop: - Sort toolbar toggle btn hidden when list visible; shown as << when list collapsed -
  room-list-controls buttons unified to global sort-btn class (consistent with /glosowania/ toolbar)

Layout: - Extract room-list-controls outside scrollable #room-list into separate .room-list-col
  wrapper so scrollbar never affects controls alignment - Unify padding between chat-breadcrumb-row
  and room-list-controls (.25rem .75rem) - Remove floating mobile-back-to-room button

Cleanup: - Remove dead code: onBackToRoomList, setFoldedRoomTitle, chat-show-rooms-bar viewport
  handler - Remove unused CSS: col-scrollable, list-of-rooms, list-of-pms - Remove stale ZMIANA
  labels from comments

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **chat**: Persist unsent message drafts in localStorage
  ([`36d86c2`](https://github.com/soma115/Wikikracja/commit/36d86c21e86589c78ecfd37ef8e3a3ad3b6b6810))

Drafts are saved per room on every keystroke and restored when re-entering the room. Cleared
  automatically on successful send.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **dashboard**: Reorganize tiles into 3 columns per row and fix onboarding step_voted backfill
  ([`c7e87b3`](https://github.com/soma115/Wikikracja/commit/c7e87b3bb0d17c98cd34919fed1f4853ffa53258))

Row 1: First steps | Activity | Upcoming events Row 2: Voting proposals | Discussed votings (new) |
  Active referendum Row 3: unchanged

Added discussed_proposals queryset (status=2), renamed "New proposals" to "Voting proposals" with
  Polish translations, and backfilled step_voted for users who voted before the onboarding signal
  existed.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **glosowania**: Redesign details and edit pages, clean up
  ([`de758e4`](https://github.com/soma115/Wikikracja/commit/de758e4af283c1ffec8d7207725f58ee9975d72c))

- szczegoly.html: unified single card (title + meta + action), full-width args grid, dynamic
  support/vote labels, cleaned unused imports and wrappers - edit.html: match global
  card+card-header style - components.css: detail-status-badge sizing, action-btn fit-content,
  detail-layout single column, new arg-card/form/toggle styles - django.po: add PL translations for
  new UI strings

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **nav**: Add Chat link to navigation menu
  ([`c06d19a`](https://github.com/soma115/Wikikracja/commit/c06d19ac3439d7be3830d494086e791a0f854ddb))

- **richtext**: Unify rich-text editing/rendering across tasks, glosowania, events
  ([`4d39d0d`](https://github.com/soma115/Wikikracja/commit/4d39d0df508758a9877fc0cf4b7202f92cc61e28))

Wprowadza wspólny pipeline dla pól tekstowych z minimalnym formatowaniem (B/I/U + auto-linkifikacja
  URL), współdzielony między czatem a formularzami zadań, głosowań i wydarzeń. Zastępuje ~7
  wariantów filtrów (|linebreaks, |linebreaksbr, |urlize, |safe + ad-hoc bleach.clean) jednym
  filtrem oraz jednym widgetem Django.

NOWE PLIKI - zzz/richtext.py — centralny sanityzator (bleach.clean + bleach.linkify), jedyne źródło
  prawdy: ALLOWED_TAGS = ['b','i','u','br','a'] + ALLOWED_ATTRS = {'a': ['href','rel','target']}.
  Zewnętrzne linki automatycznie dostają target="_blank" rel="noopener" przez callback. -
  home/templatetags/richtext.py — filtr {{ x|richtext }}: sanitize → \n na <br> → linkify →
  mark_safe. - home/widgets.py — RichTextWidget(forms.Textarea): contenteditable + toolbar B/I/U +
  hidden input + counter (opcjonalny). value_from_datadict() sanityzuje POST-a (defense in depth gdy
  JS wyłączony). - home/static/common/js/richtext-core.js — pure functions: getInputHtml,
  formatMessage, updateCounter, handleEnterKey, getVisibleTextLength. ALLOWED_TAGS/ATTR
  zsynchronizowane z backendem. - home/static/common/js/richtext-input.js — auto-init dla
  [data-richtext]: toolbar, skróty Ctrl+B/I/U, plain-text paste, sync hidden input przy submit.

REFAKTOR CZATU (zero zmian zachowania) - chat/consumers.py: usunięta lokalna stała
  ALLOWED_HTML_TAGS, dwa wywołania bleach.clean(...) zamienione na sanitize(..., linkify=False). -
  chat/services.py: usunięte 3 martwe importy (bleach, settings, format_chat_message), dwa
  re.sub(r'<[^>]+>', ...) zamienione na strip_tags(). - chat/static/chat/js/chat-core.js: pure
  functions (getInputHtml, formatMessage, updateCounter, handleEnterKey, getVisibleTextLength)
  przeniesione do /static/common/js/richtext-core.js. chat-core.js teraz je re-eksportuje, więc
  chat.js / chat-embedded.js / handlers.js / domapi.js działają bez zmian.

ZASTOSOWANIE W FORMULARZACH - tasks: TaskForm.description → RichTextWidget. Szablony task_form.html
  (+ {{form.media}}), task_detail.html, _task_card.html, _task_cards.html używają |richtext zamiast
  |linebreaks(br)|safe. - glosowania: DecyzjaForm.tresc/kara/uzasadnienie + ArgumentForm.content →
  RichTextWidget z max_length. Szablony szczegoly.html (5 wystąpień), _proposal_card.html (3),
  delete_argument.html (1) → |richtext. dodaj.html / edit.html / edit_argument.html ładują
  {{form.media}}. Inline formularze argumentów FOR/AGAINST w szczegoly.html zostawione na plain
  <textarea> (sanityzacja na POST przez ArgumentForm.value_from_datadict). - events:
  EventForm.description → RichTextWidget. event_detail.html / event_list.html → |richtext.
  event_form.html ładuje {{form.media}}.

POLA Z TINYMCE — CELOWO NIETKNIĘTE (zaufana treść admina/długie teksty) - board.post.text — TinyMCE
  + |safe (bez zmian). - elibrary.book.abstract — używa TinyMCE poprzez static/js/uploader.js
  (tinymce.init({selector:'textarea'})) ładowane w book_form.html. KOREKTA: book_list.html i
  book_detail.html teraz renderują {{...|safe}} zamiast escape'owanego tekstu (wcześniej tagi
  <p>/<strong> wyświetlały się jako tekst). UpdateBookForm pozostaje na forms.Textarea — TinyMCE
  zamienia ją client-side. - home.start.text, home.footer.text, activity.description — bez zmian
  (treść redagowana w panelu admina, dozwolony pełen HTML).

GLOBALNIE - home/templates/home/base.html: DOMPurify ładowany raz globalnie (używany i przez chat
  input, i przez RichTextWidget). Usunięte duplikaty <script> z chat.html, _embedded_chat.html oraz
  z RichTextWidget.Media.

LOKALIZACJA - locale/pl/LC_MESSAGES/django.po: zaktualizowane numery linii po nowych blokach {%
  block extra_css %} w szablonach formularzy + dodane polskie tłumaczenie nowego placeholdera w
  opisie zadania.

DOZWOLONE TAGI (backend ↔ frontend, jedno źródło prawdy) b, i, u, br, a (z atrybutami
  href/rel/target) Reszta (np. <p>, <strong>, <script>) wycinana przez bleach.clean (backend) i
  DOMPurify (frontend).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>

- **tasks**: Add category field with multi-select JS filter and tooltips
  ([`52c2348`](https://github.com/soma115/Wikikracja/commit/52c2348efebabc04e457b40cc555fe65d7cee09c))

- Task.Category with 7 choices + CATEGORY_DESCRIPTIONS dict (gettext_lazy) - Migration
  0007_add_task_category - Category field in task create/edit form with [i] popover listing all
  categories - Multi-select dropdown filter in toolbar: JS DOM filtering + pushState URL sync, no
  reload - Fix cache invalidation: version-key pattern replaces broken delete_pattern - Fix dropdown
  panel closing on click via stopPropagation - Popover and dropdown styled with project design
  tokens (--bg-card, --accent) - PL and EN translations for all category labels and descriptions

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- Modularize chat functionality by extracting core features into chat-core.js
  ([`5b8c2c5`](https://github.com/soma115/Wikikracja/commit/5b8c2c5a9b355f713b2d6d9c4cc79ffcc44f08b7))

- **chat**: Apply compose-box layout to embedded chat view
  ([`c28ea24`](https://github.com/soma115/Wikikracja/commit/c28ea24a4ed67deaeced8ec669171a6f3199a7a2))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **chat**: Introduce ChatRepository and simplify consumer logic
  ([`20b7ec1`](https://github.com/soma115/Wikikracja/commit/20b7ec1399449ccaa9f4267e0ca11cd8819c0da0))

Refactor chat consumers to use a repository pattern via ChatRepository, removing direct model
  imports and cleaning up unused code and comments for better maintainability and readability.

- **chat**: Modularize event handlers by utilizing shared functions from chat-core.js
  ([`b7e8eaf`](https://github.com/soma115/Wikikracja/commit/b7e8eaf617fb3774b728cefc5957bb467db16b73))

- **chat**: Redesign compose bar into unified input box
  ([`22c6ea8`](https://github.com/soma115/Wikikracja/commit/22c6ea84f4e17ddec24c8b891001ca24cc7c811b))

Move send button and formatting toolbar into a single rounded compose-box container below the
  textarea, matching new UI design.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **push-notifications**: Migrate VAPID public key handling to dynamic settings
  ([`379a2a7`](https://github.com/soma115/Wikikracja/commit/379a2a74259061e474fce3ecb72b664320100167))


## v1.0.0 (2026-04-25)

### Bug Fixes

- 1 ASGI thred in debug mode
  ([`e19f579`](https://github.com/soma115/Wikikracja/commit/e19f579c5ef9e8de4f86f7d83b1d61cbd68ca96a))

- Add allowed users to room on creation to prevent race condition in create_one2one_rooms
  ([`025a6c8`](https://github.com/soma115/Wikikracja/commit/025a6c807eba2ec24e700907ae7fd821638ae2fd))

- Add database transaction with select_for_update lock to prevent race conditions in user activation
  ([`a70494b`](https://github.com/soma115/Wikikracja/commit/a70494b8536e21f9228f185dbb9cc3eb5a50ad28))

- Add detailed logging for room access checks and improve fix_room_permissions command output
  ([`7fc33f6`](https://github.com/soma115/Wikikracja/commit/7fc33f63619e799931d49db82ab3eb3c68cfa04f))

- Add DoesNotExist exception handling with logging to chat consumers, glosowania views, and
  obywatele views
  ([`b8ed394`](https://github.com/soma115/Wikikracja/commit/b8ed39402b1dc587a9c2e27be88063cc1e5a7662))

- Add None reputation check and logging to activate_eligible_users, return 0 on population error
  ([`d3a223b`](https://github.com/soma115/Wikikracja/commit/d3a223b818966b1f893ecc2e1f5cbc7d84a5bb38))

- Add orphaned Uzytkownik cleanup and logging to duplicate email migration
  ([`82168d7`](https://github.com/soma115/Wikikracja/commit/82168d7cc43a6127327dbf53db1e82b0156a60ef))

- Add Room ManyToMany cleanup for orphaned users in duplicate email migration
  ([`d039fbd`](https://github.com/soma115/Wikikracja/commit/d039fbd2e0f2f75f7341bfe01e245e3f42f6c9ab))

- Added explicit id declaration in models for coe quality
  ([`fb898da`](https://github.com/soma115/Wikikracja/commit/fb898da1df94ba9da16d55afbd4288e9aed2b75f))

- Adjust scheduler intervals - chat_messages to 12,18h, chat_rooms and count_citizens to every 5
  minutes, update_site to minute 2
  ([`74720e0`](https://github.com/soma115/Wikikracja/commit/74720e069aca58268fe0d85cd7e091f97b7228de))

- All translations
  ([`42c90ae`](https://github.com/soma115/Wikikracja/commit/42c90aebba404a86ad9a9267a8b30d8fd8e5251d))

- Chat js circular dependency resolved
  ([`6f04b8e`](https://github.com/soma115/Wikikracja/commit/6f04b8e38d96c6fc5076bb9b5a640b5097224328))

- Chat optimization, no WebSock if not subscribed
  ([`47e9f94`](https://github.com/soma115/Wikikracja/commit/47e9f94c7cf9eb4998cc0866e9a7a2e8bc00049f))

- Cron day of week
  ([`c343412`](https://github.com/soma115/Wikikracja/commit/c34341217cac57beaea72cb1bd7a7054b4707db0))

- Cssy poprawnie zmergowane
  ([`39fdbda`](https://github.com/soma115/Wikikracja/commit/39fdbdaaa5e9b2c43a9ecd2490767ea274c0825a))

- Deleted unused files
  ([`bee21a0`](https://github.com/soma115/Wikikracja/commit/bee21a059fad558ae0800d726d6dcec5e9684dae))

- Dont show (and force) unseen archived rooms, Default: collapsed
  ([`6d492b1`](https://github.com/soma115/Wikikracja/commit/6d492b19e89568c8524b7258ce5a87fcabcbde6a))

- Escape regex pattern and remove duplicate email migrations
  ([`aaeef90`](https://github.com/soma115/Wikikracja/commit/aaeef901af50a842035b4b662a50ce9880adad2a))

- Exclude archived rooms from new message notifications and remove unused imports
  ([`6715e6e`](https://github.com/soma115/Wikikracja/commit/6715e6efa491aeccce6b934118c3246c43496381))

- Get_messages optimizations
  ([`719396f`](https://github.com/soma115/Wikikracja/commit/719396fe7519b46bc64c6928145e837b240201c5))

- Hide scheduler.lock
  ([`6b58ad6`](https://github.com/soma115/Wikikracja/commit/6b58ad66c74425c8262d71196efa0bdeb31ddb6c))

- Implement activity feed read marking functionality and update unread item handling
  ([`aba76a3`](https://github.com/soma115/Wikikracja/commit/aba76a3c641d85dd822eac33cffff166f611ef4b))

- Improve user activation logging and prevent duplicate activations in count_citizens command
  ([`55829d2`](https://github.com/soma115/Wikikracja/commit/55829d21f464969ec670e86d016cd7bc68d7c456))

- Improve user handling with case-insensitive email check, safer signal handlers, and optimized
  query
  ([`3295844`](https://github.com/soma115/Wikikracja/commit/3295844a7e0f40e28e5ed863c73a8990c393fd52))

- In docker scheduler runs twice, file lock added
  ([`b6c2814`](https://github.com/soma115/Wikikracja/commit/b6c28147f4819b28653fb5bcc292fb6d32c275e5))

- Just formatted chat.css
  ([`6037c04`](https://github.com/soma115/Wikikracja/commit/6037c049a57c7f477336ab76ab490e37d0305dc4))

- Less logging
  ([`32c45f3`](https://github.com/soma115/Wikikracja/commit/32c45f3fb6e986d01351ea4e69a3a6d282eb7168))

- Minor html fixes
  ([`15e1ecc`](https://github.com/soma115/Wikikracja/commit/15e1eccbaae4d9cfecac598d0cd5fa72e0020ecf))

- Move scheduler singleton check from apps.py to scheduler.py and return existing instance
  ([`64f55b5`](https://github.com/soma115/Wikikracja/commit/64f55b568da965105ad86adb2e7160d80e56af45))

- No negative req reputation
  ([`4d05e6c`](https://github.com/soma115/Wikikracja/commit/4d05e6cb8a52b88b0fdb39778cae9260985a3c31))

- One websocket connection for notif and chat
  ([`f69197e`](https://github.com/soma115/Wikikracja/commit/f69197ef391e45243fe831f1a82df31b7295b753))

- Optimized get-notifications-data
  ([`1b46166`](https://github.com/soma115/Wikikracja/commit/1b461664a05f70774d34a4837034b494914b160f))

- Python 3.14 migration fix, dead library
  ([`ca41b24`](https://github.com/soma115/Wikikracja/commit/ca41b245ab6a96512e1d589d9e6d7fc6c49fbe99))

- Remove outdated security documentation files after fixes have been applied to codebase
  ([`4879c01`](https://github.com/soma115/Wikikracja/commit/4879c018446b3e2dc5724011172b43340226b40c))

- Removed redudant index
  ([`0f1a16e`](https://github.com/soma115/Wikikracja/commit/0f1a16e2a8283981d315f17f4234468c7044e259))

- Room list not showing
  ([`1064efd`](https://github.com/soma115/Wikikracja/commit/1064efddfe1aeeb043d0fc789937a73a32ba5c40))

- Set reputation to 0 for users without ratings and move save outside conditional
  ([`91f44c0`](https://github.com/soma115/Wikikracja/commit/91f44c0963471006ad04c5d1f84aa317ef83233c))

- Update translation files with new line numbers after DoesNotExist exception handling changes
  ([`da59ff9`](https://github.com/soma115/Wikikracja/commit/da59ff95d806cd4e8900ca479b6e40dc5aa7271c))

- Update translation files with new line numbers after settings.py changes
  ([`32100a8`](https://github.com/soma115/Wikikracja/commit/32100a899af87b89a6f5d976a8f6b2e097b648df))

- Updated github workflow actions versions
  ([`60c8419`](https://github.com/soma115/Wikikracja/commit/60c84199907c7c150fbbd6954342f3e1ec24e173))

- Wider Zasoby screen
  ([`13dc811`](https://github.com/soma115/Wikikracja/commit/13dc81147d1b3053e89968b93ce56c962e665066))

### Chores

- Js and css cleanings
  ([`f180822`](https://github.com/soma115/Wikikracja/commit/f180822a5a27884d00a4309b16374118dae0554b))

- Updated requerements
  ([`99aad8c`](https://github.com/soma115/Wikikracja/commit/99aad8cd7e2e540452809e14bd868b52fffab0e8))

### Features

- Add 'why' field to profile display and form handling.
  ([`3f44a34`](https://github.com/soma115/Wikikracja/commit/3f44a3437c9cfe1c64ad40684bf64be99149b62a))

- Add 'why' field to profile display and form handling. Part 2.
  ([`6607d12`](https://github.com/soma115/Wikikracja/commit/6607d12176eb1124efd1b0d02ccbdfa3507ab834))

- Add duplicate email validation and handling in signup form
  ([`2e808cd`](https://github.com/soma115/Wikikracja/commit/2e808cd2f112cf3619f9d86beb2e499ea33d83dc))

- Android Firebase notifications
  ([`84e093e`](https://github.com/soma115/Wikikracja/commit/84e093efc2bad930c5e80bde15dc2ddd13b27174))

- Android firebase notifications almost work
  ([`be2907c`](https://github.com/soma115/Wikikracja/commit/be2907c3dc157eb4ed6ff264ae2fce55b5989eac))

- Chat mobile view like discord/messenger, not yet perfect
  ([`086ad46`](https://github.com/soma115/Wikikracja/commit/086ad46d38451e2fc7397f9ee94e715dbd99b4b5))

- Efficient browser hot reload
  ([`d1390d7`](https://github.com/soma115/Wikikracja/commit/d1390d78eeaa9146ecfac85bea695b35e35409a1))

- Fix starting daphne
  ([`0ba826e`](https://github.com/soma115/Wikikracja/commit/0ba826e2d125ecb960c44eb61c5c035c60fa6467))

- Minor translation fix
  ([`81bffad`](https://github.com/soma115/Wikikracja/commit/81bffad6d80f46ba66b8fd362e1faac3f3b34bcf))

- More chat performance impovements
  ([`110d813`](https://github.com/soma115/Wikikracja/commit/110d8131ab943ea7a614a4bc4fd72de2ec7c9e73))

- Moved chat rooms management into scheduler, added debug toolbar, count_citizens every 10 mins
  ([`70fcc55`](https://github.com/soma115/Wikikracja/commit/70fcc55f976c49a3485be3ac73a10787c0f81051))

- New icon unSee in rooms
  ([`0e08fbe`](https://github.com/soma115/Wikikracja/commit/0e08fbe5fa234a97cb02703174e016fbba86ec33))

- Packages removed and updated, DEBUG settings adjusted
  ([`92c1496`](https://github.com/soma115/Wikikracja/commit/92c1496f5fc9310761509b60e4161440a36d8a3e))

- Push notif, PWA, logs
  ([`28da10b`](https://github.com/soma115/Wikikracja/commit/28da10b86bc40dc85f1463c849d757bcf124d244))

- Show votes count for user
  ([`fe7b4c3`](https://github.com/soma115/Wikikracja/commit/fe7b4c36233078e933fb81d79bbeb456c9a25bba))

- Standarize logging
  ([`d7a6745`](https://github.com/soma115/Wikikracja/commit/d7a6745a6309545845cedd196574d2ffcfb21dbd))

- Support hashed/versioned static files
  ([`9776760`](https://github.com/soma115/Wikikracja/commit/9776760d4abb96b675ff4f2a8c9cc6d22c4ac4df))

- Update bootstrap to 5, jquery to 4, chat ui, base
  ([`16ce09a`](https://github.com/soma115/Wikikracja/commit/16ce09a82db87eefed538275b695b77fb8f92f95))

- Warn: DB CHANGE! Implement voting system using JSONField in Message model and migrate existing
  votes
  ([`31ec94d`](https://github.com/soma115/Wikikracja/commit/31ec94d77daec26afaabb2c8fdcdaa553765fe63))

- Warn: DB CHANGE! Implement voting system using JSONField in Message model and migrate existing
  votes
  ([`2a1b018`](https://github.com/soma115/Wikikracja/commit/2a1b018e69f4e479c0e019a485f256552f795cf9))

- Yapf formatter, ruff linter and import sorter
  ([`ea9e90a`](https://github.com/soma115/Wikikracja/commit/ea9e90acfeda9b998d3f1ef859b80f65c18d5123))
