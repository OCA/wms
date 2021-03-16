context("Profile mgmt", () => {
    before(() => {
        // TODO: move this to common action
        // Fake login
        window.sessionStorage.setItem(
            "shopfloor_apikey",
            JSON.stringify({value: Cypress.config("TEST_API_KEY")})
        );
        window.sessionStorage.setItem(
            "shopfloor_authenticated",
            JSON.stringify({value: Cypress.config("TEST_API_KEY")})
        );
        // Reset profile
        window.sessionStorage.removeItem("shopfloor_profile");
    });

    it("Open profile settings", () => {
        cy.visit("#/settings");
        cy.get("button[data-action=setting-profile]").click();
        cy.url().should("include", "#/profile");
    });

    it("Select profile", () => {
        cy.get(".list-item-wrapper:first :checkbox").as("profile");
        cy.get("@profile").then(profile => {
            let profile_id = profile.val();
            profile.click();
            cy.location().should(loc => {
                expect(loc.hash).to.eq("#/");
            });
            cy.get("[data-ref=session-detail-profile]").should(
                "have.attr",
                "data-id",
                profile_id
            );
        });
    });
});
