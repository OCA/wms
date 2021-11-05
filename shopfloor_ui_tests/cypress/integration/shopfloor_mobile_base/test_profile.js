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

    describe("Selects a profile", () => {
        // NOTE: This part of the test covers multiple different features
        // as cypress erases the cookies between each test
        // and the session_id cookie is required in many of them.
        // Do not split it as it will break the test.

        it("Navigates to the profile list and selects a profile", () => {
            // Logs in
            const auth_type = Cypress.env("auth_type");
            cy.get_credentials("correct", auth_type).then((credentials) => {
                credentials =
                    auth_type === "user"
                        ? [
                              {name: "username", value: credentials.username},
                              {name: "password", value: credentials.password},
                          ]
                        : [{name: "apikey", value: credentials.apikey}];
                cy.intercept_user_config();
                cy.login(credentials);

                // Waits for user_config call
                cy.wait_for({expect_success: true, request_name: "user_config"}).then(
                    (res) => {
                        // Goes to the profile page and checks the list of profiles
                        cy.url().should("eq", Cypress.config("baseUrl"));
                        cy.get(".text-center").children("button").click();
                        cy.contains("Profile -", {matchCase: false}).click();
                        const expected_profiles = ["Demo Profile 1", "Demo Profile 2"];
                        cy.check_profile_list(expected_profiles);

                        // Clicks on 'Demo Profile 1'
                        cy.intercept_menu_request();

                        const profiles = res.response.body.data.profiles;
                        const profile = profiles.filter(
                            (profile) => profile.name === "Demo Profile 1"
                        )[0];

                        cy.activate_profile(profile);

                        // Waits for menu call and tests the outcome
                        cy.wait_for_profile_data().then((res) => {
                            const menu_data = {
                                profile: profile,
                                menus: res.response.body.data.menus,
                            };
                            cy.compare_sessionStorage_profiles(menu_data);

                            cy.url().should("eq", Cypress.config("baseUrl"));

                            Cypress.env("test_menu_data", menu_data);
                        });
                    }
                );
            });
        });
    });
    describe("Test profiles", () => {
        describe("Test profile 'Demo Profile 1'", () => {
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
});
