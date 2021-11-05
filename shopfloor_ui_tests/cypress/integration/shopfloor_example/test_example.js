describe("Test to make sure that handling different profiles works as expected", () => {
    before(() => {
        cy.visit(Cypress.config("baseUrl") + "login");
        cy.get("form").then(($form) => {
            if ($form.find("input[name='apikey']").length) {
                Cypress.env("auth_type", "apikey");
            } else {
                Cypress.env("auth_type", "user");
            }
        });
    });

    describe("Fake login", () => {
        it("Logs in", () => {
            const auth_type = Cypress.env("auth_type");
            cy.fake_login(auth_type);
        });
        it("Goes to the profile page", () => {
            cy.visit(Cypress.config("baseUrl") + "profile");
            cy.url().should("eq", Cypress.config("baseUrl") + "profile");

            const expected_profiles = ["Partner manager"];
            cy.check_profile_list(expected_profiles);
        });
    });
    describe("Test profile 'Partner manager'", () => {
        it("Selects profile and makes sure the information in session storage corresponds with the information received from the request", () => {
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
        });
    });
});
