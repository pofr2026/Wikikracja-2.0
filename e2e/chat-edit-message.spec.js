// Regresja: po edycji wiadomości w treści pojawia się literalny tekst "… pokaż więcej".
// Przyczyna: setEditing pobierał innerHTML z .msg-text (czyli całą strukturę .expandable z
// dokleconym .expandable-hint "… pokaż więcej"), bo dataset.raw nie był ustawiany przy batch
// insert (historia/replace) — tylko w addMessage. Edytor dostawał HTML expandable, user wysyłał
// go z powrotem, backend zapisywał razem z tekstem hint'a.
//
// Fix: data-raw="<%=raw_message%>" jako atrybut template'u .msg-text — single source of truth
// dla każdej ścieżki renderu (addMessage, batch insert, replaceMessages, history scroll-back).
const { test, expect } = require('@playwright/test');

async function enterFirstRoom(page) {
    await page.goto('/chat/?view=rooms');
    await page.waitForSelector('.room-link', { timeout: 10000 });
    await page.evaluate(() => {
        document.querySelectorAll('.nav-cat-btn[aria-expanded="false"]').forEach(b => b.click());
    });
    await page.waitForTimeout(400);
    const roomLink = page.locator('.room-link').first();
    await expect(roomLink).toBeVisible();
    await roomLink.click();
    await expect(roomLink).toHaveClass(/joined/, { timeout: 10000 });
    await page.waitForSelector('.messages', { timeout: 10000 });
}

async function sendMessage(page, text) {
    const input = page.locator('#message-input');
    await input.click();
    await input.fill(text);
    await page.locator('.send-message').click();
    // Czekamy aż wiadomość trafi do DOM (own + treść) — wracamy z return tego elementu.
    const ownMessages = page.locator('.message.own .msg-text', { hasText: text });
    await expect(ownMessages.last()).toBeVisible({ timeout: 10000 });
    return ownMessages.last();
}

async function editOwnMessage(page, originalText, appendedText) {
    // Klik edit na ostatniej wiadomości pasującej do originalText.
    const msgDiv = page.locator('.message.own', { has: page.locator('.msg-text', { hasText: originalText }) }).last();
    await msgDiv.locator('.edit-message').click();
    // Input jest contenteditable — typujemy na końcu (focus już przeniesiony przez setEditing).
    const input = page.locator('#message-input');
    await expect(input).toBeFocused();
    // Przesuwamy kursor na koniec i dopisujemy.
    await input.press('End');
    await input.pressSequentially(appendedText);
    await page.locator('.send-message').click();
}

test.describe('chat — edycja wiadomości nie wstrzykuje markera "pokaż więcej" do treści', () => {
    test.use({ viewport: { width: 1280, height: 800 } });

    test('desktop: edycja wiadomości wysłanej w tej sesji nie zostawia "pokaż więcej" w treści', async ({ page }, testInfo) => {
        test.skip(testInfo.project.name !== 'desktop-chromium', 'Desktop-only test');
        await enterFirstRoom(page);

        const stamp = Date.now();
        const original = `Krótka treść testowa ${stamp}`;
        const appended = ' edytowane';
        await sendMessage(page, original);
        await editOwnMessage(page, original, appended);

        // Po edycji: szukamy wiadomości po finalnej treści. Treść NIE może zawierać "pokaż więcej".
        const edited = page.locator('.message.own .msg-text', { hasText: `${original}${appended}` }).last();
        await expect(edited).toBeVisible({ timeout: 10000 });
        const text = await edited.locator('.expandable-body').innerText();
        expect(text).not.toContain('pokaż więcej');
        expect(text.trim()).toBe(`${original}${appended}`);
    });

    test('desktop: edycja wiadomości załadowanej z historii (po reload) nie zostawia "pokaż więcej"', async ({ page }, testInfo) => {
        test.skip(testInfo.project.name !== 'desktop-chromium', 'Desktop-only test');
        await enterFirstRoom(page);

        const stamp = Date.now();
        const original = `Wiadomość z historii ${stamp}`;
        const appended = ' edytowane-z-historii';
        await sendMessage(page, original);

        // Reload: po reentry wiadomość przychodzi z batch insert (historia), nie z addMessage.
        // To ścieżka która regress'owała — dataset.raw nie był ustawiany.
        await page.reload();
        await page.waitForSelector(`.message.own .msg-text:has-text("${original}")`, { timeout: 10000 });

        await editOwnMessage(page, original, appended);

        const edited = page.locator('.message.own .msg-text', { hasText: `${original}${appended}` }).last();
        await expect(edited).toBeVisible({ timeout: 10000 });
        const text = await edited.locator('.expandable-body').innerText();
        expect(text).not.toContain('pokaż więcej');
        expect(text.trim()).toBe(`${original}${appended}`);
    });
});
