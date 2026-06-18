/**
 * @jest-environment jsdom
 *
 * Regression tests for chat notification favicon handling.
 */

const fs = require('fs');
const path = require('path');

function loadUtilityModule() {
    const source = fs
        .readFileSync(path.join(__dirname, '..', 'utility.js'), 'utf8')
        .replace(/\bexport\s+/g, '');
    const moduleScope = {};
    const wrapper = new Function('moduleScope', `
        ${source}
        moduleScope.changeIcon = changeIcon;
        moduleScope.removeNotification = removeNotification;
    `);
    wrapper(moduleScope);
    return moduleScope;
}

describe('chat notification favicon', () => {
    beforeEach(() => {
        document.head.innerHTML = '';
        document.body.innerHTML = '';
    });

    test('removeNotification restores the page favicon instead of the static chat fallback', () => {
        const brandedFavicon = '/media/site_branding/derived/favicon.ico?v=12345';
        document.head.innerHTML = `<link rel="icon" type="image/x-icon" href="${brandedFavicon}">`;
        const { changeIcon, removeNotification } = loadUtilityModule();

        changeIcon('/static/chat/images/notification-on.ico');
        expect(document.querySelector("link[rel~='icon']").getAttribute('href'))
            .toBe('/static/chat/images/notification-on.ico');

        removeNotification();

        expect(document.querySelector("link[rel~='icon']").getAttribute('href'))
            .toBe(brandedFavicon);
    });
});
