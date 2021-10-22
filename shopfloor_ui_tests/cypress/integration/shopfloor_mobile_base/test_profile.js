describe("Test to make sure that handling different profiles works as expected", () => {
    describe("Fake login", () => {
        it("Recreates log in", () => {
            cy.fake_login();
        });
        it("Goes to the page with the list of profiles", () => {
            cy.visit(Cypress.config("baseUrl") + "profile");
            cy.url().should("eq", Cypress.config("baseUrl") + "profile");
            cy.check_profile_list();
        });
    });
    describe("Test profiles", () => {
        describe("Test profile 'Demo Profile 1'", () => {
            it("Selects profile and makes sure the information in session storage corresponds with the information received from the request", () => {
                cy.activate_profile("Demo Profile 1");
            });
            it("Checks that the correct scenarios appear in the page", () => {
                cy.check_profile_scenarios();
                cy.check_sidebar_scenarios();
            });
            it("Goes back to the page with the list of profiles", () => {
                cy.sidebar_menu_to("settings");
                cy.contains("Profile -", {matchCase: false}).click();
            });
        });
        describe("Test profile 'Partner manager'", () => {
            it("Selects profile and makes sure the information in session storage corresponds with the information received from the request", () => {
                cy.reset_local_profiles_info();
                cy.activate_profile("Partner manager");
            });
            it("Checks that the correct scenarios appear in the page", () => {
                cy.check_profile_scenarios();
                cy.check_sidebar_scenarios();
            });
            it("Opens scenario", () => {
                cy.open_scenario("partner_example");
            });
            it("Closes scenario", () => {
                cy.close_scenario();
            });
            it("Goes back to the page with the list of profiles", () => {
                cy.sidebar_menu_to("settings");
                cy.contains("Profile -", {matchCase: false}).click();
                cy.reset_local_profiles_info();
            });
        });
    });
});
