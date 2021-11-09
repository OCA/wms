describe("Test to make sure that handling different profiles works as expected", () => {
    // This test covers the access to the different profiles
    // of the application, their selection and how they display
    // their different scenarios.

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
            check_profile_list(expected_profiles);
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
                intercept_menu_request();

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
                    cy.url().should("eq", Cypress.config("baseUrl"));

                    const menu_data = Cypress.env("test_menu_data");
                    compare_sessionStorage_profiles(menu_data);
                    Cypress.env("test_menu_data", menu_data);
                });
                it("Checks that the correct scenarios appear in the page", () => {
                    check_profile_scenarios();
                    check_menu_items();
                });
                it("Goes back to the profile page", () => {
                    cy.sidebar_menu_to("settings");
                    cy.contains("Profile -", {matchCase: false}).click();
                });
            });
        });
    }
});

// Test-specific functions

const compare_sessionStorage_profiles = (data) => {
    cy.window().then((win) => {
        const profile = JSON.parse(win.sessionStorage.getItem("shopfloor_profile"))
            .value;
        const appmenu = JSON.parse(win.sessionStorage.getItem("shopfloor_appmenu"))
            .value;

        if (JSON.stringify(profile) !== JSON.stringify(data.profile)) {
            throw new Error(
                "The profile information stored in the session storage doesn't match the response from the request"
            );
        }
        if (JSON.stringify(appmenu.menus) !== JSON.stringify(data.menus)) {
            throw new Error(
                "The menus information stored in the session storage doesn't match the response from the request"
            );
        }
    });
};

const check_menu_items = () => {
    const menus = Cypress.env("test_menu_data").menus;
    menus.forEach((menu) => {
        cy.get(".v-navigation-drawer__content").children().contains(menu.name);
    });
};

const check_profile_scenarios = () => {
    const menu_data = Cypress.env("test_menu_data");
    menu_data.menus.forEach((menu) => {
        cy.contains(menu.name);
        cy.contains(`Scenario: ${menu.scenario}`);
    });
};

const check_profile_list = (profiles) => {
    profiles.forEach((profile) => {
        cy.contains(profile, {matchCase: false});
    });
};

const intercept_menu_request = () => {
    cy.intercept({
        method: "POST",
        url: "*/user/menu",
    }).as("profile_data");
};
