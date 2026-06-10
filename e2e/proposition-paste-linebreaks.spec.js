// Weryfikacja regresji: paste tekstu z pustymi liniami w RichTextWidget formularza
// "Nowy przepis" nie powinno produkować nadmiarowych <br> w wysyłanym HTML.
//
// Przed fix'em w richtext-core.js: paste "A\n\nB" generował hidden value "A<br><br><br>B"
// (browser auto-wrappował tekst w <div> bloki z filler <br>, a serializer dodawał drugi
// <br> dla bloku). Po fix'cie: "A<br><br>B" (jedno br = nowa linia, drugie = pusta linia).

const { test, expect } = require('@playwright/test');

test('paste z pustymi liniami w propozycji daje poprawne <br> w hidden input', async ({ page }) => {
    await page.goto('/glosowania/nowy/');
    await page.waitForSelector('.richtext-wrapper');

    const trescWrapper = page.locator('.richtext-wrapper').filter({
        has: page.locator('input[type="hidden"][name="tresc"]'),
    });
    const editor = trescWrapper.locator('.richtext-input');
    await editor.click();

    // Symuluj paste przez ClipboardEvent z DataTransfer — bypass clipboard permissions.
    await editor.evaluate((el) => {
        const dt = new DataTransfer();
        dt.setData('text/plain', 'A\n\nB\nC');
        el.dispatchEvent(new ClipboardEvent('paste', {
            clipboardData: dt,
            bubbles: true,
            cancelable: true,
        }));
    });

    const hiddenValue = await trescWrapper.locator('input[type="hidden"][name="tresc"]').inputValue();
    expect(hiddenValue).toBe('A<br><br>B<br>C');
});

test('paste z Windows line endings (CRLF) daje ten sam wynik co LF', async ({ page }) => {
    await page.goto('/glosowania/nowy/');
    await page.waitForSelector('.richtext-wrapper');

    const trescWrapper = page.locator('.richtext-wrapper').filter({
        has: page.locator('input[type="hidden"][name="tresc"]'),
    });
    const editor = trescWrapper.locator('.richtext-input');
    await editor.click();

    await editor.evaluate((el) => {
        const dt = new DataTransfer();
        dt.setData('text/plain', 'A\r\n\r\nB\r\nC');
        el.dispatchEvent(new ClipboardEvent('paste', {
            clipboardData: dt,
            bubbles: true,
            cancelable: true,
        }));
    });

    const hiddenValue = await trescWrapper.locator('input[type="hidden"][name="tresc"]').inputValue();
    expect(hiddenValue).toBe('A<br><br>B<br>C');
});
