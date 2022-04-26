import "cypress-localstorage-commands";

Cypress.Commands.add("fake_login", (auth_type, login_data) => {
    cy.fixture("app_config.json").then((data) => {
        data.user_info = login_data || data.user_info;
        window.sessionStorage.setItem(
            "shopfloor_appconfig",
            JSON.stringify({value: data})
        );
    });

    cy.fixture(`credentials_${auth_type}.json`).then((data) => {
        const apikey = data.filter((item) => item.name === "correct")[0].apikey;
        login_data = login_data || apikey;
        window.sessionStorage.setItem(
            "shopfloor_apikey",
            JSON.stringify({value: login_data})
        );
    });

    window.sessionStorage.setItem(
        "shopfloor_authenticated",
        JSON.stringify({value: true})
    );
});

Cypress.Commands.add("get_session_storage", (item) => {
    cy.window().its("sessionStorage").invoke("getItem", item);
});

Cypress.Commands.add("clear_input_fields", (field_names) => {
    field_names.forEach((field_name) => {
        cy.get(`input[name=${field_name}]`).clear();
    });
});

Cypress.Commands.add(
    "wait_for",
    ({expect_success = true, reload = false, request_name = ""}) => {
        if (reload) {
            cy.reload();
        }

        cy.wait(`@${request_name}`).then((res) => {
            if (expect_success && res.response.statusCode !== 200) {
                throw new Error(
                    `Request ${request_name} returned a status of ${res.response.statusCode}. It should have returned a status of 200`
                );
            }
            if (!expect_success && res.response.statusCode < 400) {
                throw new Error(
                    `Request ${request_name} returned a status of ${res.response.statusCode}. It should have returned an error status`
                );
            }
            return res;
        });
    }
);

Cypress.Commands.add("intercept_user_config_request", () => {
    cy.intercept({
        method: "POST",
        url: "**/app/user_config",
    }).as("user_config");
});

Cypress.Commands.add("prepare_test_authentication", () => {
    cy.visit(Cypress.config("baseUrl") + "login");
    cy.get("form").then(($form) => {
        const auth_type = Cypress.env("auth_type");
        cy.get_credentials("correct", auth_type).then((credentials) => {
            credentials =
                auth_type === "user"
                    ? [
                          {name: "username", value: credentials.username},
                          {name: "password", value: credentials.password},
                      ]
                    : [{name: "apikey", value: credentials.apikey}];
            Cypress.env("credentials", credentials);
        });
    });
});

Cypress.Commands.add("get_credentials", (name, auth_type) => {
    cy.fixture(`credentials_${auth_type}.json`).then((data) => {
        return data.filter((item) => item.name === name)[0];
    });
});

Cypress.Commands.add("login", (credentials) => {
    credentials.forEach((entry) => {
        cy.get(`input[name=${entry.name}]`).type(entry.value);
    });
    cy.get('button[type="submit"]').click();
});

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
        const localstorage_appconfig = JSON.parse(
            win.sessionStorage.getItem("shopfloor_appconfig")
        ).value;
        const test_appconfig = Cypress.env("test_appconfig").data;

        if (JSON.stringify(localstorage_appconfig) !== JSON.stringify(test_appconfig)) {
            throw new Error(
                "The user's information doesn't match the information in the response received from the login request"
            );
        }
    });
});

Cypress.Commands.add("sidebar_menu_to", (toClick = "") => {
    cy.get(".v-toolbar__content").children("button").click();
    cy.get('a[href="#/"]');
    cy.get('a[href="#/settings"]');
    cy.get('a[href="#/scan_anything"]');
    cy.get(`a[href="#/${toClick}"]`).click();
    cy.get("header").click({force: true});
});

Cypress.Commands.add("activate_profile", (profile) => {
    cy.get(`input[value=${profile.id}]`).parent().click();
    // TODO: Find a better alternative for the below timeout.
    // It is currently needed to give time for
    // the backend to complete its processes
    // before going on with the rest of the test.
    cy.wait(500);
});
