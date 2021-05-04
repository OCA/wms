// ***********************************************
// https://on.cypress.io/custom-commands
// ***********************************************
//
//

Cypress.Commands.add("reset_storage", () => {
    // Reset app state
    window.sessionStorage.removeItem("shopfloor_apikey");
    window.sessionStorage.removeItem("shopfloor_authenticated");
    window.sessionStorage.removeItem("shopfloor_appconfig");
    cy.reset_app_data("profile");
    cy.reset_app_data("appmenu");
});

function reset_app_data(key) {
    if (key) {
        window.sessionStorage.removeItem("shopfloor_" + key);
    } else {
        ["apikey", "authenticated", "appconfig", "appmenu"].forEach(reset_app_data);
    }
}
Cypress.Commands.add("reset_app_data", key => {
    reset_app_data(key);
});

Cypress.Commands.add("fake_login", key => {
    key = key || Cypress.config("TEST_API_KEY");
    // Fake login
    window.sessionStorage.setItem("shopfloor_apikey", JSON.stringify({value: key}));
    window.sessionStorage.setItem(
        "shopfloor_authenticated",
        JSON.stringify({value: true})
    );
});

Cypress.Commands.add("manual_login", key => {
    key = key || Cypress.config("TEST_API_KEY");
    cy.visit("#/login");
    cy.get("input[name=apikey]").type(key);
    cy.get("form").submit();
});

Cypress.Commands.add("go_to_profile_settings", () => {
    cy.visit("#/settings");
    cy.get("button[data-action=setting-profile]").click();
});

Cypress.Commands.add("set_profile", (index = 1) => {
    cy.go_to_profile_settings();
    cy.get(".list-item-wrapper:nth(" + index + ") :checkbox").as("profile");
    return cy.get("@profile").click();
});
