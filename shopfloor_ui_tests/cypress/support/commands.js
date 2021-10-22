// General commands

Cypress.Commands.add("fake_login", (login_data) => {
    const auth_type = Cypress.env("auth_type");
    const test_data = Cypress.config("TEST_AUTH_DATA");

    cy.fixture("app_config_test.json")
        .as("app_config_test")
        .then((data) => {
            window.sessionStorage.setItem(
                "shopfloor_appconfig",
                JSON.stringify({value: data})
            );
            cy.get_session_storage("shopfloor_appconfig").should("exist");
        });

    window.sessionStorage.setItem(
        "shopfloor_authenticated",
        JSON.stringify({value: true})
    );
    cy.get_session_storage("shopfloor_authenticated").should("exist");

    if (auth_type === "apikey") {
        login_data = login_data || test_data.auth_api_key;
        window.sessionStorage.setItem(
            "shopfloor_apikey",
            JSON.stringify({value: login_data})
        );
        cy.get_session_storage("shopfloor_apikey").should("exist");
    }
});

Cypress.Commands.add("get_session_storage", (item) => {
    cy.window().its("sessionStorage").invoke("getItem", item);
});

Cypress.Commands.add("reset_storage", (keys) => {
    keys.forEach((key) => window.sessionStorage.removeItem(`shopfloor_${key}`));
});

Cypress.Commands.add("clear_input_fields", (field_names) => {
    field_names.forEach((field_name) => {
        cy.get(`input[name=${field_name}]`).clear();
    });
});

// Commands for the authentication tests

Cypress.Commands.add("get_credentials", (name, auth_type) => {
    if (name !== "correct" && auth_type === "user") {
        cy.fixture("credentials_user.json")
            .as("user_entries")
            .then((users) => {
                const user = users.filter((user) => user.name === name)[0];

                return {
                    username: user.username,
                    password: user.password,
                };
            });
    } else if (name !== "correct" && auth_type === "apikey") {
        cy.fixture("credentials_api_key.json")
            .as("keys")
            .then((keys) => {
                const key = keys.filter((key) => key.name === name)[0];

                return {
                    apikey: key.api_key,
                };
            });
    } else if (name === "correct" && auth_type === "user") {
        const credentials = Cypress.config("TEST_AUTH_DATA").auth_user_credentials;
        return {
            username: credentials.username,
            password: credentials.password,
        };
    } else {
        const apikey = Cypress.config("TEST_AUTH_DATA").auth_api_key;
        return {
            apikey,
        };
    }
});

Cypress.Commands.add("attempt_login", (name) => {
    const auth_type = Cypress.env("auth_type");

    cy.get_credentials(name, auth_type).then((data) => {
        if (auth_type === "user") {
            if (data.username) {
                cy.get('input[name="username"]')
                    .type(data.username)
                    .should("have.value", data.username);
            } else {
                cy.get('input[name="username"]').should("have.value", "");
            }

            if (data.password) {
                cy.get('input[name="password"]')
                    .type(data.password)
                    .should("have.value", data.password);
            } else {
                cy.get('input[name="password"]').should("have.value", "");
            }
        } else {
            if (data.apikey) {
                cy.get('input[name="apikey"]')
                    .type(data.apikey)
                    .should("have.value", data.apikey);
            } else {
                cy.get('input[name="apikey"]').should("have.value", "");
            }
        }
        cy.get('button[type="submit"]').click();
    });
});

Cypress.Commands.add("intercept_user_config", () => {
    cy.intercept({
        method: "POST",
        url: "*/app/user_config",
    }).as("user_config");
});

Cypress.Commands.add(
    "wait_for_user_config",
    ({expect_success = false, reload = false}) => {
        if (reload) {
            cy.reload();
        }

        cy.wait("@user_config").then((res) => {
            if (expect_success && res.response.statusCode !== 200) {
                throw new Error(
                    `Request 'user_config' returned a status of ${res.response.statusCode}. It should have returned a status of 200`
                );
            }
            if (!expect_success && res.response.statusCode < 400) {
                throw new Error(
                    `Request 'user_config' returned a status of ${res.response.statusCode}. It should have returned an error status`
                );
            }
            return res;
        });
    }
);

Cypress.Commands.add("compare_sessionStorage_authentication", () => {
    cy.window().then((win) => {
        const authenticated = JSON.parse(
            win.sessionStorage.getItem("shopfloor_authenticated")
        ).value;
        if (!authenticated) {
            throw new Error(
                "The user isn't authenticated in session storage (shopfloor_authenticated)"
            );
        }

        cy.readFile("cypress/fixtures/app_config.json").then((test_appconfig) => {
            const appconfig = JSON.parse(
                win.sessionStorage.getItem("shopfloor_appconfig")
            ).value;
            if (JSON.stringify(appconfig) !== JSON.stringify(test_appconfig)) {
                throw new Error(
                    "The user's information doesn't match the information in the response received from the login request"
                );
            }
        });
    });
});

// Commands for the navigation tests

Cypress.Commands.add("sidebar_menu_to", (toClick = "") => {
    cy.get(".v-toolbar__content").children("button").click();
    cy.get('a[href="#/"]');
    cy.get('a[href="#/settings"]');
    cy.get('a[href="#/scan_anything"]');
    cy.get(`a[href="#/${toClick}"]`).click();
    cy.get("header").click({force: true});
});

// Commands for the profile tests

Cypress.Commands.add("check_profile_list", () => {
    cy.contains("Demo Profile 1", {matchCase: false});
    cy.contains("Demo Profile 2", {matchCase: false});
    cy.contains("Partner manager", {matchCase: false});
});

Cypress.Commands.add("activate_profile", (profile_name) => {
    cy.intercept_profile_request();
    cy.readFile("cypress/fixtures/profiles_info.json").then((data) => {
        const profile = data.profiles.filter(
            (profile) => profile.name === profile_name
        )[0];

        cy.get(`input[value=${profile.id}]`).click({force: true});

        cy.wait_for_profile_info().then((res) => {
            const data = {profile, menus: res.response.body.data.menus};
            cy.writeFile("cypress/fixtures/profiles_info.json", JSON.stringify(data));
            cy.compare_sessionStorage_profiles();
        });

        cy.get_session_storage("shopfloor_profile").should("exist");
        cy.get_session_storage("shopfloor_appmenu").should("exist");

        cy.url().should("eq", Cypress.config("baseUrl"));
    });
});

Cypress.Commands.add("check_profile_scenarios", () => {
    cy.readFile("cypress/fixtures/profiles_info.json").then((data) => {
        data.menus.forEach((menu) => {
            cy.contains(menu.name);
            cy.contains(`Scenario: ${menu.scenario}`);
        });
    });
});

Cypress.Commands.add("check_sidebar_scenarios", () => {
    cy.readFile("cypress/fixtures/profiles_info.json").then((data) => {
        data.menus.forEach((menu) => {
            cy.get(".v-navigation-drawer__content").children().contains(menu.name);
        });
    });
});

Cypress.Commands.add("open_scenario", (scenario_name) => {
    cy.get("a").contains(scenario_name).click();
    cy.url().should("include", Cypress.config("baseUrl") + scenario_name);
    cy.get("button").contains("manual selection", {matchCase: false});
});

Cypress.Commands.add("close_scenario", () => {
    cy.get("button").contains("back", {matchCase: false}).click();
    cy.url().should("eq", Cypress.config("baseUrl"));
});

Cypress.Commands.add("intercept_profile_request", () => {
    cy.intercept({
        method: "POST",
        url: "*/user/menu",
    }).as("profile_data");
});

Cypress.Commands.add("wait_for_profile_info", () => {
    cy.wait("@profile_data").then((res) => {
        return res;
    });
});

Cypress.Commands.add("reset_local_profiles_info", () => {
    cy.writeFile("cypress/fixtures/profiles_info.json", {
        profiles: [
            {
                id: 1,
                name: "Demo Profile 1",
            },
            {
                id: 2,
                name: "Demo Profile 2",
            },
            {
                id: 3,
                name: "Partner manager",
            },
        ],
    });
});

Cypress.Commands.add("compare_sessionStorage_profiles", () => {
    cy.window().then((win) => {
        const profile = JSON.parse(win.sessionStorage.getItem("shopfloor_profile"))
            .value;
        const appmenu = JSON.parse(win.sessionStorage.getItem("shopfloor_appmenu"))
            .value.menus;

        cy.readFile("cypress/fixtures/profiles_info.json").then(
            (test_profiles_info) => {
                if (
                    JSON.stringify(profile) !==
                    JSON.stringify(test_profiles_info.profile)
                ) {
                    throw new Error(
                        "The profile information stored in the session storage doesn't match the response from the request"
                    );
                }
                if (
                    JSON.stringify(appmenu) !== JSON.stringify(test_profiles_info.menus)
                ) {
                    throw new Error(
                        "The menus information stored in the session storage doesn't match the response from the request"
                    );
                }
            }
        );
    });
});
