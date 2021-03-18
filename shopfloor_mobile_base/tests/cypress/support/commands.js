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

Cypress.Commands.add("reset_profile", () => {
    window.sessionStorage.removeItem("shopfloor_profile");
});
