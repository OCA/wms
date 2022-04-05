describe("Test to make sure the navigation through the application works as expected", () => {
    // This test covers the navigation throughout the base application.
    // It includes home page, scan page and settings page.
    // The functionality of these pages is not tested here,
    // only the navigation between them.

    before(() => {
        cy.visit(Cypress.config("baseUrl") + "login");
    });

    describe("Fake login", () => {
        it("Logs in", () => {
            const auth_type = Cypress.env("auth_type");
            cy.fake_login(auth_type);
        });
        it("Goes to the home page", () => {
            cy.visit(Cypress.config("baseUrl"));
            cy.url().should("eq", Cypress.config("baseUrl"));
        });
    });
    describe("Scan", () => {
        describe("Go to scan from both the sidebar and the manifying glass icon", () => {
            it("Goes to scan from the sidebar and comes back to home", () => {
                cy.sidebar_menu_to("scan_anything");
                cy.url().should("eq", Cypress.config("baseUrl") + "scan_anything");
                cy.sidebar_menu_to("");
                cy.url().should("eq", Cypress.config("baseUrl"));
            });
            it("Goes to scan by clicking on the magnifying glass icon", () => {
                cy.get(".app-bar-actions").children("button").click();
                cy.url().should("eq", Cypress.config("baseUrl") + "scan_anything");
            });
        });
    });
    describe("Settings", () => {
        describe("Go to settings from both the sidebar and the Configure Profile button", () => {
            it("Goes to settings from the sidebar", () => {
                cy.sidebar_menu_to("settings");
                cy.url().should("eq", Cypress.config("baseUrl") + "settings");
            });
            it("Checks that it returns to scan when clicking on 'back'", () => {
                cy.contains("back", {matchCase: false}).click();
                cy.url().should("eq", Cypress.config("baseUrl") + "scan_anything");
            });
            it("Goes back to the home page", () => {
                cy.sidebar_menu_to("");
                cy.url().should("eq", Cypress.config("baseUrl"));
            });
            it("Goes to settings by clicking on the Configure Profile button", () => {
                cy.get(".text-center").children("button").click();
                cy.url().should("eq", Cypress.config("baseUrl") + "settings");
            });
        });
        describe("Languages", () => {
            it("Goes to the languages page", () => {
                cy.contains("Language -", {matchCase: false}).click();
                cy.url().should("eq", Cypress.config("baseUrl") + "language");
            });
            it("Goes back to settings", () => {
                cy.contains("back", {matchCase: false}).click();
            });
        });
        describe("Profile", () => {
            it("Goes to the profile page", () => {
                cy.contains("Profile -", {matchCase: false}).click();
                cy.url().should("eq", Cypress.config("baseUrl") + "profile");
            });
            it("Goes back to settings", () => {
                cy.contains("back", {matchCase: false}).click();
            });
        });
    });
});
