// Loguje się raz przez allauth login form i zapisuje storageState dla reszty testów.
const { test: setup, expect } = require('@playwright/test');
const path = require('path');

const STORAGE_STATE = path.join(__dirname, '.auth/user.json');

setup('login as dev user', async ({ page }) => {
    const email = process.env.E2E_EMAIL;
    const password = process.env.E2E_PASSWORD;
    if (!email || !password) {
        throw new Error('E2E_EMAIL i E2E_PASSWORD muszą być w .env.local (gitignored)');
    }

    await page.goto('/accounts/login/');
    await page.fill('input[name="login"]', email);
    await page.fill('input[name="password"]', password);

    // Click + waitForURL razem w Promise.all żeby nie czekać na pełen load ciężkiego dashboardu
    // (Daphne + websockety + 16 notyfikacji potrafi przekroczyć 30s test timeout).
    await Promise.all([
        page.waitForURL(url => !url.pathname.startsWith('/accounts/login'), { timeout: 15000 }),
        page.click('form button[type="submit"]'),
    ]);

    await page.context().storageState({ path: STORAGE_STATE });
});
