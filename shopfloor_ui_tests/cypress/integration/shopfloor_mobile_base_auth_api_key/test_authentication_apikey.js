describe("Test to make sure that the user can log in and log out using an api key", () => {
    // This test works for the apikey authentication
    // from module shopfloor_mobile_base_auth_api_key.

    before(() => {
        // TODO: when we make auth type depend on the shopfloor app backend
        // we won't need this anymore
        sessionStorage.clear();
        Cypress.env("auth_type", "api_key");
    });
    describe("Log in to the Shopfloor app", () => {
        describe("Preparation tests", () => {
            it("Checks that unauthenticated users are redirected to the Login page", () => {
                cy.intercept_user_config_request();
                cy.visit(Cypress.config("baseUrlExample"));
                cy.url().should("eq", Cypress.config("baseUrlExample") + "login");
                cy.wait("@user_config").its("response.statusCode").should("eq", 403);
            });

            it("Makes sure that the user_config or the authentication status are not in session storage", () => {
                cy.get_session_storage("shopfloor_appconfig").should("not.exist");
                cy.get_session_storage("shopfloor_authenticated").should("not.exist");
                cy.get_session_storage("shopfloor_apikey").should("not.exist");
            });
        });

        describe("Log in", () => {
            beforeEach(() => {
                const field_names = ["apikey"];

                cy.clear_input_fields(field_names);

                cy.intercept_user_config_request();
            });

            it("Attempts login with incorrect apikey", function () {
                cy.get_credentials("incorrect", "api_key").then((credentials) => {
                    cy.login([{name: "apikey", value: credentials.apikey}]);
                });
                cy.wait_for({expect_success: false, request_name: "user_config"});
            });

            it("Attempts to log in with empty apikey", function () {
                cy.get('button[type="submit"]').click();
                cy.wait_for({expect_success: false, request_name: "user_config"});
            });

            it("Logs in with correct apikey and stores the response in app_config.json", function () {
                cy.get_credentials("correct", "api_key").then((credentials) => {
                    cy.login([{name: "apikey", value: credentials.apikey}]);
                });

                cy.wait_for({expect_success: true, request_name: "user_config"}).then(
                    (res) => {
                        const data = res.response.body.data;
                        Cypress.env("test_appconfig", {data});
                    }
                );
            });
        });
    });

    describe("Tests for authenticated user", () => {
        it("Checks that the user has been redirected to the home page", () => {
            cy.url().should("eq", Cypress.config("baseUrlExample"));
        });

        it("Checks that the user's configuration, authentication status and apikey are all in the session storage", () => {
            cy.get_session_storage("shopfloor_apikey").should("exist");
            cy.get_session_storage("shopfloor_appconfig").should("exist");
            cy.get_session_storage("shopfloor_authenticated").should("exist");
        });

        it("Checks that a page reload doesn't redirect or erase the session storage info", () => {
            cy.reload();
            cy.url().should("to.not.equal", Cypress.config("baseUrlExample") + "login");

            cy.get_session_storage("shopfloor_apikey").should("exist");
            cy.get_session_storage("shopfloor_appconfig").should("exist");
            cy.get_session_storage("shopfloor_authenticated").should("exist");
        });

        it("Checks that authenticated users are redirected to the home page when trying to reach the Login page", () => {
            cy.visit(Cypress.config("baseUrlExample") + "login");
            cy.url().should("eq", Cypress.config("baseUrlExample"));
        });

        it("Checks that the information stored in the browser is identical to the information received from the server at login", () => {
            cy.compare_sessionStorage_authentication();
        });
    });

    describe("Log out", () => {
        it("Goes to the settings page", () => {
            cy.contains("configure profile", {matchCase: false}).click();
            cy.url().should("eq", Cypress.config("baseUrlExample") + "settings");
        });
        it("Logs out", () => {
            cy.contains("logout", {matchCase: false}).click();
            cy.url().should("eq", Cypress.config("baseUrlExample") + "login");
        });
        it("Has erased the storage", () => {
            cy.get_session_storage("shopfloor_apikey").should("not.exist");
            cy.get_session_storage("shopfloor_appconfig").should("not.exist");
            cy.get_session_storage("shopfloor_authenticated").should("not.exist");
        });
        it("Doesn't redirect to home after page reload", () => {
            cy.reload();
            cy.url().should("eq", Cypress.config("baseUrlExample") + "login");
        });
        it("Redirects to login if trying to acces home page", () => {
            cy.visit(Cypress.config("baseUrlExample"));
            cy.url().should("eq", Cypress.config("baseUrlExample") + "login");
        });
        it("Tests that the request to get the user's information fails as the user is not authenticated", () => {
            cy.intercept_user_config_request();
            cy.wait_for({
                expect_success: false,
                reload: true,
                request_name: "user_config",
            });
        });
    });
});
