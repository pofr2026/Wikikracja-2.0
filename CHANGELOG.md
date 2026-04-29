# CHANGELOG


## v1.1.0 (2026-04-29)

### Bug Fixes

- All translations
  ([`42c90ae`](https://github.com/soma115/Wikikracja/commit/42c90aebba404a86ad9a9267a8b30d8fd8e5251d))

- Dont show (and force) unseen archived rooms, Default: collapsed
  ([`6d492b1`](https://github.com/soma115/Wikikracja/commit/6d492b19e89568c8524b7258ce5a87fcabcbde6a))

- Implement activity feed read marking functionality and update unread item handling
  ([`aba76a3`](https://github.com/soma115/Wikikracja/commit/aba76a3c641d85dd822eac33cffff166f611ef4b))

- Set created_at on in-memory task objects in test helpers
  ([`f41d8cf`](https://github.com/soma115/Wikikracja/commit/f41d8cf2fa8c32dbf2f95ce2bfe1cf594816b4e4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Chores

- Js and css cleanings
  ([`f180822`](https://github.com/soma115/Wikikracja/commit/f180822a5a27884d00a4309b16374118dae0554b))

- Updated requerements
  ([`99aad8c`](https://github.com/soma115/Wikikracja/commit/99aad8cd7e2e540452809e14bd868b52fffab0e8))

### Features

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

- **tasks**: Add category field with multi-select JS filter and tooltips
  ([`52c2348`](https://github.com/soma115/Wikikracja/commit/52c2348efebabc04e457b40cc555fe65d7cee09c))

- Task.Category with 7 choices + CATEGORY_DESCRIPTIONS dict (gettext_lazy) - Migration
  0007_add_task_category - Category field in task create/edit form with [i] popover listing all
  categories - Multi-select dropdown filter in toolbar: JS DOM filtering + pushState URL sync, no
  reload - Fix cache invalidation: version-key pattern replaces broken delete_pattern - Fix dropdown
  panel closing on click via stopPropagation - Popover and dropdown styled with project design
  tokens (--bg-card, --accent) - PL and EN translations for all category labels and descriptions

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


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

- Escape regex pattern and remove duplicate email migrations
  ([`aaeef90`](https://github.com/soma115/Wikikracja/commit/aaeef901af50a842035b4b662a50ce9880adad2a))

- Exclude archived rooms from new message notifications and remove unused imports
  ([`6715e6e`](https://github.com/soma115/Wikikracja/commit/6715e6efa491aeccce6b934118c3246c43496381))

- Get_messages optimizations
  ([`719396f`](https://github.com/soma115/Wikikracja/commit/719396fe7519b46bc64c6928145e837b240201c5))

- Hide scheduler.lock
  ([`6b58ad6`](https://github.com/soma115/Wikikracja/commit/6b58ad66c74425c8262d71196efa0bdeb31ddb6c))

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

- Yapf formatter, ruff linter and import sorter
  ([`ea9e90a`](https://github.com/soma115/Wikikracja/commit/ea9e90acfeda9b998d3f1ef859b80f65c18d5123))
