context("Test 1st access to app", () => {
    before(() => {
        cy.reset_storage();
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
