describe("Test to make sure that handling different profiles works as expected", () => {
    before(() => {
        cy.prepare_test_authentication().then(() => {
            const credentials = Cypress.env("credentials");

            cy.intercept_user_config_request();
            cy.login(credentials);
        });
        cy.wait_for({expect_success: true, request_name: "user_config"}).then((res) => {
            cy.url().should("eq", Cypress.config("baseUrl"));
            cy.get(".text-center").children("button").click();
            cy.contains("Profile -", {matchCase: false}).click();
            const expected_profiles = ["Demo Profile 1", "Demo Profile 2"];
            cy.check_profile_list(expected_profiles);
            Cypress.env("test_appconfig", res.response.body.data.profiles);
        });
    });

    beforeEach(() => {
        Cypress.Cookies.preserveOnce("session_id");
    });

    // Runs the test twice (once per Demo Profile).

    for (let i = 1; i <= 2; i++) {
        describe("Select profile", () => {
            it(`Selects Demo Profile ${i}`, () => {
                cy.intercept_menu_request();

                const profiles = Cypress.env("test_appconfig");
                const profile = profiles.filter(
                    (profile) => profile.name === `Demo Profile ${i}`
                )[0];

                cy.activate_profile(profile);

                cy.wait_for({
                    expect_success: true,
                    request_name: "profile_data",
                }).then((res) => {
                    const menu_data = {
                        profile: profile,
                        menus: res.response.body.data.menus,
                    };
                    Cypress.env("test_menu_data", menu_data);
                });
            });
        });
        describe("Profile tests", () => {
            describe(`Test profile 'Demo Profile ${i}'`, () => {
                it("Checks the page is redirected and the local information was stored correctly", () => {
                    const menu_data = Cypress.env("test_menu_data");

                    cy.compare_sessionStorage_profiles(menu_data);

                    cy.url().should("eq", Cypress.config("baseUrl"));

                    Cypress.env("test_menu_data", menu_data);
                });
                it("Checks that the correct scenarios appear in the page", () => {
                    cy.check_profile_scenarios();
                    cy.check_sidebar_scenarios();
                });
                it("Goes back to the profile page", () => {
                    cy.sidebar_menu_to("settings");
                    cy.contains("Profile -", {matchCase: false}).click();
                });
            });
        });
    }
});
