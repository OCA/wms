context("Profile mgmt", () => {
    before(() => {
        cy.fake_login();
        cy.reset_app_data("profile");
    });

    it("Open profile settings", () => {
        cy.go_to_profile_settings();
        cy.url().should("include", "#/profile");
    });

    it("Select profile", () => {
        cy.set_profile().then(profile => {
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
