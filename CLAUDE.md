# Zasady pracy z Claude — projekt Wikikracja

## 1. Zawsze pytaj przed kodowaniem

Przed jakąkolwiek akcją (kodowanie, edycja, komendy) najpierw:

1. Napisz 2-4 zdania opisujące co zrozumiałeś z polecenia.
2. Wyjaśnij co planujesz zrobić i dlaczego (które pliki, jakie podejście).
3. Przed wykonaniem komendy shell — wyjaśnij po polsku co ona robi i po co.
4. Zasugeruj najlepszy model do zadania:
   - **Sonnet** — typowe zadania (CRUD, UI, migracje, refactor)
   - **Opus** — złożona architektura, wielosystemowa analiza, skomplikowana logika biznesowa
5. Zasugeruj ustawienia modelu jeśli relevantne: extended thinking (dla złożonej logiki), effort level (low/medium/high).
6. Zakończ pytaniem potwierdzającym (Tak ✓) — nie zaczynaj pracy bez potwierdzenia.

**Dlaczego:** User chce łapać nieporozumienia wcześnie, zanim zmarnujemy tokeny.

---

## 2. Czyszczenie kodu przed commitem

Po zakończeniu każdego zadania, PRZED commitem i pushem, zaproponuj:

1. Usunięcie zbędnych restek — tymczasowe zmienne, debug logi, zakomentowane linie.
2. Aktualizację komentarzy — zostaw/uaktualnij TYLKO te, które pomagają zrozumieć kod nawet osobie mało technicznej.

**Dlaczego:** Czysty kod przed commitem zmniejsza review time i poprawia jakość PR-a.

---

## 3. DOMPurify — ładowany globalnie

DOMPurify jest ładowany jako klasyczny `<script>` w `home/templates/home/base.html` — **nie importować go jako ES module**.

- Dostęp przez `window.DOMPurify` z guardem: `typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(html, {...}) : html`
- Dotyczy każdego miejsca gdzie sanityzujemy HTML od użytkownika (chat, RichTextWidget, i wszystko nowe).

---

## 4. Sugestia modelu

Zawsze informuj jeśli zadanie wymaga przełączenia na wyższy model (Opus), z krótkim uzasadnieniem. User chce świadomie zarządzać kosztami i jakością.

---

## 5. Design system — single source of truth

Wszystkie zmiany frontendowe muszą korzystać z istniejących CSS variables. Nigdy nie hardcodować kolorów, spacingów ani fontów bezpośrednio.

**Główne pliki:**
- `home/static/home/css/app.css` — główny plik (1483 linii): CSS variables dla 4 tematów, Bootstrap overrides, komponenty UI, layout
- `chat/static/chat/css/chat.css` — semantic tokens dla chata (aliasy globalnych zmiennych)
- `home/templates/home/base.html` — ładuje CSS, inicjalizuje temat, anti-FOUC script

**4 tematy:** `dark` (domyślny), `light`, `civic`, `official` — przełączane przez `data-theme` atrybut na `<html>`.

**Theme toggle:** `window.applyTheme(theme)` w `home/static/home/js/app.js` — zapisuje wybór w `localStorage['app-theme']`.

**Zasady:**
- Kolory, spacing, zaokrąglenia, tranzycje — zawsze przez zmienne CSS (`:root { --nazwa: wartość }`)
- Nowe komponenty definiuj w `app.css`, nie w plikach per-widok
- Nowy temat = nowy blok `[data-theme="nazwa"]` nadpisujący zmienne z `:root`
- Bootstrap overrides przez `--bs-*` variables, nie przez !important
