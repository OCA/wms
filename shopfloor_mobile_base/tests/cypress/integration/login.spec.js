context("Test 1st access to app", () => {
    before(() => {
        // Reset app state
        // TODO: move this to common action
        window.sessionStorage.removeItem("shopfloor_apikey");
        window.sessionStorage.removeItem("shopfloor_authenticated");
        window.sessionStorage.removeItem("shopfloor_appconfig");
    });

    it("Load app as anon and login", () => {
        cy.visit("#/");
        cy.url().should("include", "#/login");
        cy.get("input[name=apikey]").type(Cypress.config("TEST_API_KEY"));
        cy.get("form").submit();
        cy.get("[data-ref=profile-not-ready]").should("exist");
    });

    it("Profile required -> Settings", () => {
        cy.get("[data-ref=profile-not-ready]")
            .find("button")
            .click();
        cy.url().should("include", "#/settings");
    });
});
