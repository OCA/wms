describe("Test to make sure that the user can log in and log out", () => {
    // This test works for both apikey and standard (username / password) authentication.
    // The test detects the type of credentials expected in the login form
    // and takes the appropriate credentials from the config file (cypress.json).
    // This means that modules shopfloor_mobile_base_auth_user and
    // shopfloor_mobile_base_auth_api_key can be tested with it.

    describe("Log in to the Shopfloor app", () => {
        describe("Preparation tests", () => {
            it("Checks that unauthenticated users are redirected to the Login page", () => {
                cy.visit(Cypress.config("baseUrl"));
                cy.url().should("eq", Cypress.config("baseUrl") + "login");
            });

            it("Checks that the request to user_config fails (user is not authenticated)", () => {
                cy.intercept_user_config();
                cy.wait_for_user_config({reload: true});
            });

            it("Makes sure that the user_config or the authentication status are not in session storage", function () {
                cy.get_session_storage("shopfloor_appconfig").should("not.exist");
                cy.get_session_storage("shopfloor_authenticated").should("not.exist");
                cy.get_session_storage("shopfloor_apikey").should("not.exist");
            });
        });

        describe("Log in", () => {
            before(() => {
                cy.get("form").then(($form) => {
                    if ($form.find("input[name='apikey']").length) {
                        Cypress.env("auth_type", "apikey");
                    } else {
                        Cypress.env("auth_type", "user");
                    }
                });
            });
            beforeEach(() => {
                const auth_type = Cypress.env("auth_type");
                const field_names =
                    auth_type === "user" ? ["username", "password"] : ["apikey"];

                cy.clear_input_fields(field_names);
                cy.intercept_user_config();
            });

            it("Attempts login with incorrect credentials", function () {
                cy.attempt_login("incorrect");
                cy.wait_for_user_config({});
            });

            it("Attempts to log in with empty credentials", function () {
                cy.attempt_login("empty");
                cy.wait_for_user_config({});
            });

            it("Logs in with correct credentials and stores the response in app_config.json", function () {
                cy.attempt_login("correct");
                cy.wait_for_user_config({expect_success: true}).then((res) => {
                    const data = res.response.body.data;
                    cy.writeFile(
                        "cypress/fixtures/app_config.json",
                        JSON.stringify(data)
                    );
                });
            });
        });
    });

    describe("Tests for authenticated user", () => {
        it("Checks that the user has been redirected to the home page", () => {
            cy.url().should("eq", Cypress.config("baseUrl"));
        });

        // TODO: check if this test belongs here
        it("Checks that a profile hasn't been selected yet", () => {
            cy.get("[data-ref=profile-not-ready]").should("exist");
        });

        it("Checks that the user's configuration and authentication status are both in the session storage", () => {
            cy.get_session_storage("shopfloor_appconfig").should("exist");
            cy.get_session_storage("shopfloor_authenticated").should("exist");
        });

        it("Checks that a page reload doesn't redirect or erase the user's info", () => {
            cy.reload();
            cy.url().should("to.not.equal", Cypress.config("baseUrl") + "login");

            cy.get_session_storage("shopfloor_appconfig").should("exist");
            cy.get_session_storage("shopfloor_authenticated").should("exist");
        });

        it("Checks that authenticated users are redirected to the home page when trying to reach the Login page", () => {
            cy.visit(Cypress.config("baseUrl") + "login");
            cy.url().should("eq", Cypress.config("baseUrl"));
        });

        it("Checks that the information stored in the browser is identical to the information received from the server at login", () => {
            cy.compare_sessionStorage_authentication();
        });
    });

    describe("Log out", () => {
        it("Goes to the settings page", () => {
            cy.contains("configure profile", {matchCase: false}).click();
            cy.url().should("eq", Cypress.config("baseUrl") + "settings");
        });
        it("Logs out", () => {
            cy.contains("logout", {matchCase: false}).click();
            cy.url().should("eq", Cypress.config("baseUrl") + "login");
        });
        it("Has erased the storage", () => {
            cy.get_session_storage("shopfloor_appconfig").should("not.exist");
            cy.get_session_storage("shopfloor_authenticated").should("not.exist");

            cy.writeFile("cypress/fixtures/app_config.json", {
                _comment:
                    "Do not delete this file, it is used to handle data during the authentication tests",
            });
        });
        it("Doesn't redirect to home after page reload", () => {
            cy.reload();
            cy.url().should("eq", Cypress.config("baseUrl") + "login");
        });
        it("Redirects to login if trying to acces home page", () => {
            cy.visit(Cypress.config("baseUrl"));
            cy.url().should("eq", Cypress.config("baseUrl") + "login");
        });
        it("Tests that the request to get the user's information fails as the user is not authenticated", () => {
            cy.intercept_user_config();
            cy.wait_for_user_config({reload: true});
        });
    });
});
