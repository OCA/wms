context("Test 1st access to app", () => {
    before(() => {
        cy.reset_storage();
    });

    it("Load app as anon and login", () => {
        cy.visit("#/");
        cy.url().should("include", "#/login");
        cy.manual_login();
        cy.get("[data-ref=profile-not-ready]").should("exist");
    });

    it("Profile required -> Settings", () => {
        cy.get("[data-ref=profile-not-ready]")
            .find("button")
            .click();
        cy.url().should("include", "#/settings");
    });
});
