// Bug fix verify: na mobile klik w już aktywny pokój z rozwiniętej listy zwija listę.
// Zmiana: chat/static/chat/js/handlers.js (handleRoomLinkClick early-return po klasie "joined").
const { test, expect } = require('@playwright/test');

async function setupChatPage(page) {
    // ?view=rooms → decideStartupAction zwraca joinAction='none' (no auto-join).
    // Bez tego chat wskakuje w pierwszy public room → na mobile od razu room-active + lista hidden.
    await page.goto('/chat/?view=rooms');
    await page.waitForSelector('.room-link', { timeout: 10000 });
    // Rozwiń wszystkie kategorie (na mobile często collapsed). evaluate() klika synchronicznie
    // wszystkie naraz — bez tego per-locator iteracja wpada w race condition gdy lista się przeklika.
    await page.evaluate(() => {
        document.querySelectorAll('.nav-cat-btn[aria-expanded="false"]').forEach(b => b.click());
    });
    // Buffer na animację Bootstrap collapse — bez tego room-link bywa "not stable" przy kliku.
    await page.waitForTimeout(400);
    // Pierwszy room-link bez visible filter — locator musi pozostać valid PO wejściu w pokój
    // (na mobile room-active hideuje .room-list-col, :visible przestałby matchować ten sam element).
    const roomLink = page.locator('.room-link').first();
    await expect(roomLink).toBeVisible();
    return roomLink;
}

test.describe('chat mobile — room list collapse on tap of active room', () => {
    test('mobile: klik aktywnego pokoju z rozwiniętej listy zdejmuje room-list-showing', async ({ page }, testInfo) => {
        // Tylko mobile-chromium. Na desktop project ten test się nie odpala (feature jest mobile-only przez guard window.innerWidth < 768).
        test.skip(testInfo.project.name !== 'mobile-chromium', 'Mobile-only test');
        const roomLink = await setupChatPage(page);
        const chatRooms = page.locator('.chat-rooms');

        // 1. Klik w pokój — wchodzi do niego (mobile: lista znika, wiadomości fullscreen)
        await roomLink.click();
        await expect(chatRooms).toHaveClass(/room-active/, { timeout: 10000 });
        await expect(chatRooms).not.toHaveClass(/room-list-showing/);
        await expect(roomLink).toHaveClass(/joined/);

        // 2. Klik w >> (toggle-room-list-btn) — pokazuje listę nad aktywnym pokojem
        await page.locator('#toggle-room-list-btn').click();
        await expect(chatRooms).toHaveClass(/room-list-showing/);
        await expect(chatRooms).toHaveClass(/room-active/);

        // 3. KLUCZOWE: klik w ten sam pokój → lista ma się zwinąć, room-active zostaje
        await roomLink.click();
        await expect(chatRooms).not.toHaveClass(/room-list-showing/);
        await expect(chatRooms).toHaveClass(/room-active/);
    });
});

test.describe('chat desktop — guard: aktywny pokój nie zdejmuje room-list-showing', () => {
    test.use({ viewport: { width: 1280, height: 800 } });

    test('desktop: klik aktywnego pokoju nie usuwa room-list-showing (gdyby była)', async ({ page }, testInfo) => {
        // Tylko desktop-chromium. Mobile project ma device descriptor Pixel 5 (mobile UA + touch);
        // sam override viewportu nie zmienia device i daje hybrydę myląco zieloną.
        test.skip(testInfo.project.name !== 'desktop-chromium', 'Desktop-only test');
        const roomLink = await setupChatPage(page);
        const chatRooms = page.locator('.chat-rooms');

        // Wejdź do pokoju i POCZEKAJ na pełen async flow (websocket join → showFoldedRoomHeader)
        await roomLink.click();
        await expect(roomLink).toHaveClass(/joined/, { timeout: 10000 });
        await expect(chatRooms).toHaveClass(/room-active/);

        // Sztucznie dodaj room-list-showing (symulacja stanu który mógłby przyjść z forceListVisible+mobileShowList)
        await chatRooms.evaluate(el => el.classList.add('room-list-showing'));
        await expect(chatRooms).toHaveClass(/room-list-showing/);

        // Klik w aktywny pokój — NA DESKTOPIE klasa room-list-showing ma zostać (guard window.innerWidth < 768).
        // expect.toHaveClass auto-poll'uje (default 5s) — daje czas na ewentualny side-effect, który NIE powinien nadejść.
        await roomLink.click();
        await expect(chatRooms).toHaveClass(/room-list-showing/);
    });
});
