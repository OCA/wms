// General commands

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
    ({expect_success = false, reload = false, request_name = ""}) => {
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

// Intercept commands

Cypress.Commands.add("intercept_user_config_request", () => {
    cy.intercept({
        method: "POST",
        url: "*/app/user_config",
    }).as("user_config");
});

Cypress.Commands.add("intercept_login_request", () => {
    cy.intercept({
        method: "POST",
        url: "*/auth/login",
    }).as("login");
});

Cypress.Commands.add("intercept_menu_request", () => {
    cy.intercept({
        method: "POST",
        url: "*/user/menu",
    }).as("profile_data");
});

Cypress.Commands.add("intercept_partner_list_request", () => {
    cy.intercept({
        method: "GET",
        url: "*/partner_example/partner_list*",
    }).as("partner_list");
});

Cypress.Commands.add("intercept_single_partner_detail_request", () => {
    cy.intercept({
        method: "GET",
        url: "*/partner_example/detail/*",
    }).as("single_partner_detail");
});

Cypress.Commands.add("intercept_partner_scan_request", () => {
    cy.intercept({
        method: "GET",
        url: "*/partner_example/scan/*",
    }).as("partner_scan");
});

// Authentication commands

Cypress.Commands.add("prepare_test_authentication", () => {
    cy.visit(Cypress.config("baseUrl") + "login");
    cy.get("form").then(($form) => {
        if ($form.find("input[name='apikey']").length) {
            Cypress.env("auth_type", "apikey");
        } else {
            Cypress.env("auth_type", "user");
        }
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

// Navigation commands

Cypress.Commands.add("sidebar_menu_to", (toClick = "") => {
    cy.get(".v-toolbar__content").children("button").click();
    cy.get('a[href="#/"]');
    cy.get('a[href="#/settings"]');
    cy.get('a[href="#/scan_anything"]');
    cy.get(`a[href="#/${toClick}"]`).click();
    cy.get("header").click({force: true});
});

// Profile and Scenario commands

Cypress.Commands.add("check_profile_list", (profiles) => {
    profiles.forEach((profile) => {
        cy.contains(profile, {matchCase: false});
    });
});

Cypress.Commands.add("activate_profile", (profile) => {
    cy.get(`input[value=${profile.id}]`).parent().click();
    cy.wait(500);
});

Cypress.Commands.add("check_profile_scenarios", () => {
    const menu_data = Cypress.env("test_menu_data");
    menu_data.menus.forEach((menu) => {
        cy.contains(menu.name);
        cy.contains(`Scenario: ${menu.scenario}`);
    });
});

Cypress.Commands.add("check_sidebar_scenarios", () => {
    const menus = Cypress.env("test_menu_data").menus;
    menus.forEach((menu) => {
        cy.get(".v-navigation-drawer__content").children().contains(menu.name);
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

Cypress.Commands.add("compare_sessionStorage_profiles", (data) => {
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
});

// Commands for shopfloor_example

Cypress.Commands.add("test_partner_card", () => {
    const record = Cypress.env("test_current_partner");
    cy.get(".detail-partner_example").contains(record.name);
    cy.get(".detail-partner_example").contains(`Ref: ${record.id}`);
    cy.get(".detail-partner_example").contains(`Email: ${record.email}`);
});

Cypress.Commands.add("scan_partner", (id) => {
    cy.intercept_partner_scan_request();
    cy.get("input").type(id);
    cy.get("form").submit();
    cy.wait_for({expect_success: true, request_name: "partner_scan"}).then((res) => {
        const record = res.response.body.data.detail.record;
        Cypress.env("test_current_partner", record);
    });
});

Cypress.Commands.add("check_page_contains_partners", (partners) => {
    partners.forEach((partner) => {
        cy.contains(partner.name, {matchCase: false});
    });
});
