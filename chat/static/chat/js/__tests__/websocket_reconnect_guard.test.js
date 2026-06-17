/**
 * @jest-environment jsdom
 *
 * Testy guardu wysylki w oknie reconnectu (websocket-manager.js).
 * Kontekst buga: ReconnectingWebSocket.send() rzuca surowy string
 * 'INVALID_STATE_ERR : Pausing to reconnect websocket' gdy wewnetrzny socket jest
 * null (po onclose, przed wznowieniem). Bez guardu ten rzut wbijal sie do
 * onRoomTryJoin -> alert(error) jako straszny popup, a w sendJsonAsync zostawial
 * zawieszona (nigdy nierozwiazana) obietnice w rejestrze promises.
 *
 * DLACZEGO minimalna kopia zamiast importu realnych modulow: jest.config.js ma
 * `transform: {}` (brak Babel/ts-jest), a pliki produkcyjne sa ES modules.
 * To swiadomy dlug testowy: trzymamy tu tylko kontrakt reconnect/drop, a
 * docelowo warto przejsc na import realnych modulow po wlaczeniu ESM w Jescie.
 */

// Keep copied controllers minimal: test reconnect/drop contracts, not full UI modules.

// Minimalna kopia kontraktu z websocket-manager.js (synchronizowac przy zmianie!).
function makeManager(socket) {
    const promises = {};
    function isReconnectSendError(err) {
        const name = err?.name || '';
        const message = typeof err === 'string' ? err : (err?.message || '');
        return name === 'InvalidStateError'
            || message.includes('INVALID_STATE_ERR : Pausing to reconnect websocket')
            || message.includes('InvalidStateError');
    }
    const api = {
        socket,
        promises, // wystawione tylko na potrzeby asercji w tescie
        sendJson(obj) {
            if (socket.readyState !== WebSocket.OPEN) {
                console.warn("sendJson dropped while socket not OPEN (reconnecting):", obj.command);
                return false;
            }
            const payload = JSON.stringify(obj);
            try {
                socket.send(payload);
            } catch (err) {
                if (!isReconnectSendError(err)) throw err;
                console.warn("sendJson dropped on socket.send race (reconnecting):", obj.command);
                return false;
            }
            return true;
        },
        sendJsonAsync(obj) {
            if (socket.readyState !== WebSocket.OPEN) {
                return Promise.reject('NOT_CONNECTED');
            }
            const ID = Math.floor(Math.random() * 1000000) + 1;
            obj.__TRACE_ID = ID;
            const promise = new Promise((resolve, reject) => {
                promises[ID] = { resolve, reject };
            });
            try {
                if (this.sendJson(obj)) {
                    return promise;
                }
                delete promises[ID];
                return Promise.reject('NOT_CONNECTED');
            } catch (err) {
                delete promises[ID];
                throw err;
            }
        },
    };
    return api;
}

// Minimalny fake ReconnectingWebSocket: sterowalny readyState + licznik send.
function fakeSocket(readyState, { throwOnSend = false, sendError = null } = {}) {
    return {
        readyState,
        sentCount: 0,
        send(data) {
            if (throwOnSend) throw 'INVALID_STATE_ERR : Pausing to reconnect websocket';
            if (sendError) throw sendError;
            this.sentCount++;
            this.lastSent = data;
        },
    };
}

// ── testy ──────────────────────────────────────────────────────────────────
describe('websocket-manager guard w oknie reconnectu', () => {
    beforeEach(() => {
        // console.warn jest czescia kontraktu (drop), ale zasmieca output testow.
        jest.spyOn(console, 'warn').mockImplementation(() => {});
    });
    afterEach(() => {
        jest.restoreAllMocks();
    });

    describe('sendJsonAsync', () => {
        test('odrzuca z NOT_CONNECTED gdy socket nie jest OPEN (CONNECTING)', async () => {
            const sock = fakeSocket(WebSocket.CONNECTING);
            const mgr = makeManager(sock);
            await expect(mgr.sendJsonAsync({ command: 'join', room_id: 1 }))
                .rejects.toBe('NOT_CONNECTED');
            // nie probuje wysylac i nie zostawia zawieszonej obietnicy
            expect(sock.sentCount).toBe(0);
            expect(Object.keys(mgr.promises)).toHaveLength(0);
        });

        test('NIE rzuca synchronicznie — zawsze zwraca odrzucona obietnice', () => {
            const sock = fakeSocket(WebSocket.CLOSED);
            const mgr = makeManager(sock);
            let result;
            expect(() => { result = mgr.sendJsonAsync({ command: 'join' }); }).not.toThrow();
            expect(result).toBeInstanceOf(Promise);
            return expect(result).rejects.toBe('NOT_CONNECTED');
        });

        test('wysyla i rejestruje obietnice gdy socket OPEN', () => {
            const sock = fakeSocket(WebSocket.OPEN);
            const mgr = makeManager(sock);
            const p = mgr.sendJsonAsync({ command: 'join', room_id: 7 });
            expect(p).toBeInstanceOf(Promise);
            expect(sock.sentCount).toBe(1);
            expect(Object.keys(mgr.promises)).toHaveLength(1);
            const payload = JSON.parse(sock.lastSent);
            expect(payload.command).toBe('join');
            expect(payload.__TRACE_ID).toBeDefined();
        });

        test('defensywa: send rzuca mimo OPEN -> odrzuca i czysci rejestr promises', async () => {
            const sock = fakeSocket(WebSocket.OPEN, { throwOnSend: true });
            const mgr = makeManager(sock);
            await expect(mgr.sendJsonAsync({ command: 'join' }))
                .rejects.toBe('NOT_CONNECTED');
            expect(Object.keys(mgr.promises)).toHaveLength(0);
        });
    });

    describe('sendJson (fire-and-forget)', () => {
        test('zwraca false i nie wysyla gdy socket nie OPEN', () => {
            const sock = fakeSocket(WebSocket.CONNECTING);
            const mgr = makeManager(sock);
            expect(mgr.sendJson({ command: 'seen' })).toBe(false);
            expect(sock.sentCount).toBe(0);
        });

        test('zwraca true i wysyla gdy socket OPEN', () => {
            const sock = fakeSocket(WebSocket.OPEN);
            const mgr = makeManager(sock);
            expect(mgr.sendJson({ command: 'seen' })).toBe(true);
            expect(sock.sentCount).toBe(1);
        });

        test('wyscig: send() rzuca mimo OPEN -> zwraca false, NIE propaguje rzutu', () => {
            const sock = fakeSocket(WebSocket.OPEN, { throwOnSend: true });
            const mgr = makeManager(sock);
            let result;
            expect(() => { result = mgr.sendJson({ command: 'send' }); }).not.toThrow();
            expect(result).toBe(false);
        });

        test('nie maskuje bledu serializacji jako reconnect', () => {
            const sock = fakeSocket(WebSocket.OPEN);
            const mgr = makeManager(sock);
            const payload = { command: 'send' };
            payload.self = payload;

            expect(() => mgr.sendJson(payload)).toThrow(TypeError);
            expect(sock.sentCount).toBe(0);
        });

        test('nie maskuje nieznanego wyjatku z socket.send jako reconnect', () => {
            const sendError = new Error('programming bug in send');
            const sock = fakeSocket(WebSocket.OPEN, { sendError });
            const mgr = makeManager(sock);

            expect(() => mgr.sendJson({ command: 'send' })).toThrow(sendError);
        });

        test('sendJsonAsync czysci promise registry i rzuca dalej blad programistyczny', () => {
            const sendError = new Error('programming bug in send');
            const sock = fakeSocket(WebSocket.OPEN, { sendError });
            const mgr = makeManager(sock);

            expect(() => mgr.sendJsonAsync({ command: 'join' })).toThrow(sendError);
            expect(Object.keys(mgr.promises)).toHaveLength(0);
        });
    });
});

// handlers.js maluje optymistyczny stan przycisku PRZED onUpdateVote. Sam
// onUpdateVote nie moze robic drugiego toggle'a; ma tylko wyslac komende i cofnac
// stan wrappera, gdy wysylka padnie w oknie reconnectu.
describe('onUpdateVote — rollback optymistycznego glosu w oknie reconnectu', () => {
    // ── wierna kopia z chat.js (WS_API to modulowy singleton -> tu wstrzykiwany) ──
    let WS_API;
    async function onUpdateVote(vote, message_id, is_add) {
        const sent = is_add ? WS_API.addVote(vote, message_id) : WS_API.removeVote(vote, message_id);
        if (sent === false) {
            this?.classList.toggle('active', !is_add);
        }
    }

    function clickVote(btn, vote, message_id, is_add) {
        btn.classList.toggle('active', is_add);
        return onUpdateVote.call(btn, vote, message_id, is_add);
    }

    test('drop (sent=false) przy add: cofa toggle, przycisk wraca bez active', async () => {
        WS_API = { addVote: () => false, removeVote: () => false };
        const btn = document.createElement('button');
        await clickVote(btn, 'upvote', 1, true);
        expect(btn.classList.contains('active')).toBe(false);
    });

    test('sukces (sent=true): zachowuje optymistyczny toggle', async () => {
        WS_API = { addVote: () => true, removeVote: () => true };
        const btn = document.createElement('button');
        await clickVote(btn, 'upvote', 1, true);
        expect(btn.classList.contains('active')).toBe(true);
    });

    test('drop przy remove: przycisk z active wraca do active (cofa odznaczenie)', async () => {
        WS_API = { addVote: () => false, removeVote: () => false };
        const btn = document.createElement('button');
        btn.classList.add('active');
        await clickVote(btn, 'upvote', 1, false); // is_add=false -> removeVote
        expect(btn.classList.contains('active')).toBe(true);
    });
});

describe('WsApi mutujace wrappery zwracaja wynik sendJson', () => {
    let WS_API;

    beforeEach(() => {
        WS_API = {
            seenRoom(room_id) {
                return this.sendJson({ command: 'room-seen', room_id });
            },
            toggleReaction(reaction, message_id) {
                return this.sendJson({ command: 'message-react', reaction, message_id });
            },
            editMessage(message_id, message) {
                return this.sendJson({ command: 'edit-message', message_id, new_message: message });
            },
            toggleNotifications(room_id, enabled) {
                return this.sendJson({ command: 'toggle-notifications', room_id, enabled });
            },
            markRoomUnseen(room_id) {
                return this.sendJson({ command: 'room-unseen', room_id });
            },
        };
    });

    test('seen/notifications/unseen nie gubia false z sendJson', () => {
        WS_API.sendJson = jest.fn(() => false);

        expect(WS_API.seenRoom(7)).toBe(false);
        expect(WS_API.toggleNotifications(7, true)).toBe(false);
        expect(WS_API.markRoomUnseen(7)).toBe(false);
    });

    test('pozostale mutacje tez przepuszczaja boolean sukcesu', () => {
        WS_API.sendJson = jest.fn(() => true);

        expect(WS_API.toggleReaction('bulb', 12)).toBe(true);
        expect(WS_API.editMessage(12, 'po edycji')).toBe(true);
    });
});

describe('notification/seen — rollback optymistycznego stanu przy dropie', () => {
    const _ = (s) => s;

    function applyNotificationState(btn, enabled) {
        btn.dataset.enabled = enabled;
        const icon = btn.querySelector('i');
        icon?.classList.toggle('fa-bell', enabled);
        icon?.classList.toggle('fa-bell-slash', !enabled);
        const label = btn.querySelector('.notif-label');
        if (label) label.textContent = enabled ? _('Mute room') : _('Unmute room');
        const meta = btn.closest('.room-link')?.querySelector('.room-link__meta');
        if (meta) {
            meta.dataset.muted = enabled ? 'false' : 'true';
            let mutedIcon = meta.querySelector('.room-link__muted-icon');
            if (!enabled) {
                if (!mutedIcon) {
                    mutedIcon = document.createElement('i');
                    mutedIcon.className = 'fas fa-bell-slash room-link__muted-icon';
                    mutedIcon.title = _('Muted');
                    meta.appendChild(mutedIcon);
                }
            } else {
                mutedIcon?.remove();
            }
        }
    }

    function clickNotification(btn, sendResult) {
        const oldState = btn.dataset.enabled === 'true' || btn.dataset.enabled === true;
        const newState = !oldState;
        applyNotificationState(btn, newState);
        if (sendResult === false) {
            applyNotificationState(btn, oldState);
        }
    }

    function makeNotificationButton(enabled = true) {
        document.body.innerHTML = `
            <div class="room-link">
                <button class="notif-switch" data-room-id="7" data-enabled="${enabled}">
                    <i class="${enabled ? 'fa-bell' : 'fa-bell-slash'}"></i>
                    <span class="notif-label"></span>
                </button>
                <span class="room-link__meta" data-muted="${enabled ? 'false' : 'true'}"></span>
            </div>
        `;
        return document.querySelector('.notif-switch');
    }

    test('notification drop: przywraca dataset, ikone, label i muted meta', () => {
        const btn = makeNotificationButton(true);

        clickNotification(btn, false);

        expect(btn.dataset.enabled).toBe('true');
        expect(btn.querySelector('i').classList.contains('fa-bell')).toBe(true);
        expect(btn.querySelector('.notif-label').textContent).toBe('Mute room');
        const meta = document.querySelector('.room-link__meta');
        expect(meta.dataset.muted).toBe('false');
        expect(meta.querySelector('.room-link__muted-icon')).toBeNull();
    });

    test('notification sukces: zostawia optymistyczny stan', () => {
        const btn = makeNotificationButton(true);

        clickNotification(btn, true);

        expect(btn.dataset.enabled).toBe('false');
        expect(btn.querySelector('i').classList.contains('fa-bell-slash')).toBe(true);
        expect(document.querySelector('.room-link__meta').dataset.muted).toBe('true');
    });

    test('seen drop: przywraca klase unread i dataset przycisku', () => {
        document.body.innerHTML = `
            <div class="room-link room-not-seen" data-room-id="9">
                <button class="seen-switch" data-room-id="9" data-seen="false"></button>
            </div>
        `;
        const btn = document.querySelector('.seen-switch');
        const roomLink = document.querySelector('.room-link');

        function applySeenState(roomId, seen) {
            document.querySelector(`.room-link[data-room-id="${roomId}"]`)?.classList.toggle('room-not-seen', !seen);
            btn.dataset.seen = seen.toString();
        }

        const oldState = btn.dataset.seen === 'true';
        const newState = !oldState;
        applySeenState(btn.dataset.roomId, newState);
        applySeenState(btn.dataset.roomId, oldState);

        expect(btn.dataset.seen).toBe('false');
        expect(roomLink.classList.contains('room-not-seen')).toBe(true);
    });
});

describe('room click join retry after NOT_CONNECTED', () => {
    function makeRoomJoinController(joinRoom, action = { joinAction: 'none' }) {
        let CurrentRoomId = null;
        let PendingJoinRoomId = null;

        function rememberPendingJoinRoom(room_id) {
            const parsed = parseInt(room_id);
            PendingJoinRoomId = Number.isFinite(parsed) ? parsed : null;
        }

        function consumePendingJoinRoom() {
            const room_id = PendingJoinRoomId;
            PendingJoinRoomId = null;
            return room_id;
        }

        async function onRoomTryJoin(room_id) {
            room_id = parseInt(room_id);
            if (room_id === CurrentRoomId) {
                PendingJoinRoomId = null;
                return;
            }
            try {
                await joinRoom(room_id);
            } catch (error) {
                if (error === 'NOT_CONNECTED') {
                    localStorage.lastUsedRoomID = room_id;
                    rememberPendingJoinRoom(room_id);
                }
                return;
            }
            localStorage.lastUsedRoomID = room_id;
            PendingJoinRoomId = null;
            CurrentRoomId = room_id;
        }

        async function wsOnConnect() {
            if (CurrentRoomId) {
                const roomToRejoin = CurrentRoomId;
                CurrentRoomId = null;
                onRoomTryJoin(roomToRejoin);
                return;
            }

            const pendingJoinRoomId = consumePendingJoinRoom();
            if (pendingJoinRoomId) {
                onRoomTryJoin(pendingJoinRoomId);
                return;
            }

            if (action.joinAction === 'none') return;

            if (localStorage.lastUsedRoomID) {
                onRoomTryJoin(parseInt(localStorage.lastUsedRoomID));
            }
        }

        return {
            onRoomTryJoin,
            wsOnConnect,
            getPendingJoinRoomId: () => PendingJoinRoomId,
        };
    }

    beforeEach(() => {
        localStorage.clear();
    });

    test('clicked room is retried once on next open even when startup joinAction is none', async () => {
        const joinRoom = jest.fn()
            .mockRejectedValueOnce('NOT_CONNECTED')
            .mockResolvedValueOnce({});
        const controller = makeRoomJoinController(joinRoom, { joinAction: 'none' });

        await controller.onRoomTryJoin(7);
        await controller.wsOnConnect();
        await Promise.resolve();

        expect(joinRoom).toHaveBeenCalledTimes(2);
        expect(joinRoom).toHaveBeenNthCalledWith(2, 7);
        expect(controller.getPendingJoinRoomId()).toBeNull();
    });

    test('multiple disconnected clicks keep one latest pending room for the next open', async () => {
        const joinRoom = jest.fn()
            .mockRejectedValueOnce('NOT_CONNECTED')
            .mockRejectedValueOnce('NOT_CONNECTED')
            .mockResolvedValueOnce({});
        const controller = makeRoomJoinController(joinRoom, { joinAction: 'none' });

        await controller.onRoomTryJoin(7);
        await controller.onRoomTryJoin(8);
        await controller.wsOnConnect();
        await Promise.resolve();

        expect(joinRoom).toHaveBeenCalledTimes(3);
        expect(joinRoom).toHaveBeenNthCalledWith(3, 8);
        expect(controller.getPendingJoinRoomId()).toBeNull();
    });
});

describe('room link click seen state', () => {
    function handleRoomLinkClick(e, onRoomTryJoin) {
        if (e.target.closest('.room-link__actions')) return;
        const roomLink = e.target.closest('.room-link');
        if (!roomLink) return;
        if (roomLink.classList.contains('joined')) return;
        const room_id = roomLink.getAttribute('data-room-id');
        roomLink.classList.add('room-tapping');
        onRoomTryJoin(room_id);
    }

    test('does not mark an unread room as seen before join succeeds', () => {
        document.body.innerHTML = `
            <button class="room-link room-not-seen" data-room-id="7">
                <span class="room-name">Room</span>
            </button>
        `;
        const roomLink = document.querySelector('.room-link');
        const onRoomTryJoin = jest.fn();

        handleRoomLinkClick({ target: roomLink }, onRoomTryJoin);

        expect(onRoomTryJoin).toHaveBeenCalledWith('7');
        expect(roomLink.classList.contains('room-not-seen')).toBe(true);
    });
});

describe('embedded join — NOT_CONNECTED retry bez blokowania inputu', () => {
    const _ = (s) => s;

    function makeJoinController(ws, messagesEl, inputArea) {
        let joined = false;
        let joinRetryHandler = null;

        function retryJoinOnNextOpen() {
            if (joinRetryHandler) return;
            joinRetryHandler = function onOpen() {
                ws.socket.removeEventListener('open', joinRetryHandler);
                joinRetryHandler = null;
                joinRoom();
            };
            ws.socket.addEventListener('open', joinRetryHandler);
        }

        function joinRoom() {
            if (joined) return undefined;
            return ws.sendJsonAsync({ command: 'join', room_id: 5 })
                .then(() => {
                    joined = true;
                })
                .catch(err => {
                    if (err === 'NOT_CONNECTED') {
                        messagesEl.innerHTML = `<div class="ec-loading">${_('Connection is being restored. Waiting for reconnect...')}</div>`;
                        retryJoinOnNextOpen();
                        return;
                    }
                    messagesEl.innerHTML = `<div class="ec-loading">${_('No access to this chat.')}</div>`;
                    inputArea.style.display = 'none';
                });
        }

        return { joinRoom, isJoined: () => joined };
    }

    test('NOT_CONNECTED nie ukrywa inputu i ponawia join po kolejnym open', async () => {
        document.body.innerHTML = '<div class="messages"></div><div class="ec-input-area"></div>';
        const socket = new EventTarget();
        const ws = {
            socket,
            sendJsonAsync: jest.fn()
                .mockRejectedValueOnce('NOT_CONNECTED')
                .mockResolvedValueOnce({}),
        };
        const controller = makeJoinController(
            ws,
            document.querySelector('.messages'),
            document.querySelector('.ec-input-area')
        );

        await controller.joinRoom();

        expect(document.querySelector('.ec-input-area').style.display).not.toBe('none');
        expect(document.querySelector('.messages').textContent).toContain('Connection is being restored');
        expect(ws.sendJsonAsync).toHaveBeenCalledTimes(1);

        socket.dispatchEvent(new Event('open'));
        await Promise.resolve();
        await Promise.resolve();

        expect(ws.sendJsonAsync).toHaveBeenCalledTimes(2);
        expect(controller.isJoined()).toBe(true);
    });
});

describe('sort toolbar - rollback when fetch-messages is dropped', () => {
    function makeSortController(fetchMessages, showReconnectToast) {
        const CurrentRoomId = 7;
        let SortState = { sort_by: 'date', order: 'desc', popular_only: false };
        const appliedStates = [];

        function applyActiveStyles() {
            appliedStates.push({ ...SortState });
        }

        function refetch() {
            if (CurrentRoomId == null) return true;
            return fetchMessages(CurrentRoomId, SortState.sort_by, SortState.order, SortState.popular_only) !== false;
        }

        function rollback(previousState) {
            SortState = previousState;
            applyActiveStyles();
            showReconnectToast();
        }

        return {
            toggleSort(key) {
                const previousState = { ...SortState };
                if (SortState.sort_by === key) {
                    SortState.order = SortState.order === 'desc' ? 'asc' : 'desc';
                } else {
                    SortState.sort_by = key;
                    SortState.order = 'desc';
                }
                applyActiveStyles();
                if (!refetch()) rollback(previousState);
            },
            togglePopular() {
                const previousState = { ...SortState };
                SortState.popular_only = !SortState.popular_only;
                applyActiveStyles();
                if (!refetch()) rollback(previousState);
            },
            getState: () => ({ ...SortState }),
            getAppliedStates: () => appliedStates,
        };
    }

    test('sort change rolls back active state and shows feedback when sendJson returns false', () => {
        const fetchMessages = jest.fn(() => false);
        const showReconnectToast = jest.fn();
        const controller = makeSortController(fetchMessages, showReconnectToast);

        controller.toggleSort('likes');

        expect(fetchMessages).toHaveBeenCalledWith(7, 'likes', 'desc', false);
        expect(controller.getState()).toEqual({ sort_by: 'date', order: 'desc', popular_only: false });
        expect(controller.getAppliedStates()).toEqual([
            { sort_by: 'likes', order: 'desc', popular_only: false },
            { sort_by: 'date', order: 'desc', popular_only: false },
        ]);
        expect(showReconnectToast).toHaveBeenCalledTimes(1);
    });

    test('popular filter rolls back when fetch-messages is dropped', () => {
        const fetchMessages = jest.fn(() => false);
        const showReconnectToast = jest.fn();
        const controller = makeSortController(fetchMessages, showReconnectToast);

        controller.togglePopular();

        expect(fetchMessages).toHaveBeenCalledWith(7, 'date', 'desc', true);
        expect(controller.getState()).toEqual({ sort_by: 'date', order: 'desc', popular_only: false });
        expect(showReconnectToast).toHaveBeenCalledTimes(1);
    });
});

describe('main chat edit - dropped sendJson keeps edit mode visible', () => {
    function makeEditSubmitter(WS_API, DOM_API, showReconnectToast) {
        return async function submitEdit(message, editing_message_id) {
            if (!editing_message_id) return undefined;

            const files = DOM_API.getFiles();
            const attachments = {};
            if (files?.length) {
                attachments.images = (await WS_API.uploadFiles(files)).filenames;
            }

            const sent = WS_API.editMessage(
                editing_message_id,
                message,
                attachments,
                DOM_API.getRemovedAttachments(),
                DOM_API.getOriginalMessageText(editing_message_id)
            );
            if (sent === false) {
                showReconnectToast();
                return false;
            }
            return true;
        };
    }

    test('false result shows reconnect feedback and does not clear edit state', async () => {
        const WS_API = { editMessage: jest.fn(() => false) };
        const DOM_API = {
            getFiles: jest.fn(() => []),
            getRemovedAttachments: jest.fn(() => ['old.png']),
            getOriginalMessageText: jest.fn(() => 'before'),
            stopEditing: jest.fn(),
        };
        const showReconnectToast = jest.fn();
        const submitEdit = makeEditSubmitter(WS_API, DOM_API, showReconnectToast);

        await expect(submitEdit('after', 12)).resolves.toBe(false);

        expect(WS_API.editMessage).toHaveBeenCalledWith(12, 'after', {}, ['old.png'], 'before');
        expect(showReconnectToast).toHaveBeenCalledTimes(1);
        expect(DOM_API.stopEditing).not.toHaveBeenCalled();
    });
});
