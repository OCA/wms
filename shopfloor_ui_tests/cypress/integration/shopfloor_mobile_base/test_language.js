const _LANGUAGE_IDS = ["en-US", "fr-FR", "de-DE"];

describe("Test to make sure the user can select different languages in the app", () => {
    // This test covers the features to select language,
    // and how it is reflected in the app.

    beforeEach(() => {
        // Unlike sessionStorage, localStorage is lost before each test.
        // When updating the language, we create a snapshot using saveLocalStorage
        // and then we retrieve it before the next test.
        cy.restoreLocalStorage();
    });

    before(() => {
        sessionStorage.clear();
        cy.clearLocalStorageSnapshot();
        cy.visit(Cypress.config("baseUrlExampleDemo"));
        cy.fixture("translations").then((translations) => {
            translations.forEach((language) => {
                Cypress.env(`test_${language.id}_translations`, language);
            });
        });
    });

    describe("English is default", () => {
        describe("Checks that English is the default language", () => {
            it("Checks that no language is stored locally", () => {
                const current_language = get_stored_language();
                if (current_language) {
                    throw new Error(
                        `Language ${current_language} appears to be stored locally even though the user hasn't manually selected one yet`
                    );
                }
            });
        });
    });
    _LANGUAGE_IDS.forEach((language_id, index) => {
        describe(`Check content for ${language_id}`, () => {
            // The text that is checked for each language is:
            // - Sidebar menu: home, scan, settings
            // - Settings: language, profile, logout, back
            // - Home: configure profile

            after(() => {
                change_language(index);
                cy.saveLocalStorage();
            });
            it("Checks translations in sidebar menu", () => {
                cy.get(".v-toolbar__content").children("button").click();
                const keys = ["home", "scan", "settings"];
                check_translations(keys, language_id);
            });
            it("Refreshes to make sure the selected language persists", () => {
                cy.reload();
            });
            it("Checks translations in settings", () => {
                cy.visit(Cypress.config("baseUrlExampleDemo") + "settings");
                const keys = ["language", "profile", "logout", "back"];
                check_translations(keys, language_id);
            });
            it("Checks translations in home", () => {
                cy.visit(Cypress.config("baseUrlExampleDemo"));
                const keys = ["profile_configure"];
                check_translations(keys, language_id);
            });
        });
    });
    describe("Check that the selected language persists on logout", () => {
        it("Logs out", () => {
            cy.visit(Cypress.config("baseUrlExampleDemo") + "settings");
            cy.get("button").contains("logout", {matchCase: false}).click();
        });
        it("Checks that the language is still stored", () => {
            const language = get_stored_language();
            if (!language) {
                throw new Error(
                    "The language selected by the user did not remain stored locally after logout"
                );
            }
            if (language !== "en-US") {
                throw new Error(
                    `Language en-US was expected to be stored locally at the end of the test, but ${language} was stored instead`
                );
            }
        });
    });
});

// Test-specific functions
const get_stored_language = () => {
    const stored_current_language = window.localStorage.getItem(
        "shopfloor_current_language"
    );
    if (stored_current_language) {
        return JSON.parse(stored_current_language).value;
    }
};

const check_translations = (keys, language_id) => {
    const language_translations = Cypress.env(`test_${language_id}_translations`);
    keys.forEach((key) => {
        cy.contains(language_translations[key], {matchCase: false});
    });
};

const change_language = (index) => {
    cy.visit(Cypress.config("baseUrlExampleDemo") + "settings");
    cy.get("button[data-action='setting-language']").click();
    if (index < _LANGUAGE_IDS.length - 1) {
        // Click on the next language
        cy.get(".action.action-select")
            .eq(index + 1)
            .click();
    } else {
        // Go back to English
        cy.get(".action.action-select").first().click();
    }
};
