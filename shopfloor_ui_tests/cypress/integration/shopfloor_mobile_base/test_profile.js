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

    describe("Fake login", () => {
        it("Logs in", () => {
            const auth_type = Cypress.env("auth_type");
            cy.get_credentials("correct", auth_type).then((credentials) => {
                credentials =
                    auth_type === "user"
                        ? [
                              {name: "username", value: credentials.username},
                              {name: "password", value: credentials.password},
                          ]
                        : [{name: "apikey", value: credentials.apikey}];
                cy.login(credentials);
            });
        });
        it("Goes to the profile page", () => {
            cy.url().should("eq", Cypress.config("baseUrl"));
            cy.get(".text-center").children("button").click();
            cy.contains("Profile -", {matchCase: false}).click();
            const expected_profiles = ["Demo Profile 1", "Demo Profile 2"];
            cy.check_profile_list(expected_profiles);
        });
    });
    describe("Test profiles", () => {
        describe("Test profile 'Demo Profile 1'", () => {
            it("Selects profile and makes sure the information in session storage corresponds with the information received from the request", () => {
                cy.intercept_menu_request();
                const profiles = JSON.parse(
                    window.sessionStorage.getItem("shopfloor_appconfig")
                ).value.profiles;
                const profile = profiles.filter(
                    (profile) => profile.name === "Demo Profile 1"
                )[0];
                cy.activate_profile(profile);
                cy.wait_for_profile_data().then((res) => {
                    cy.window()
                        .its("sessionStorage")
                        .invoke("getItem", "shopfloor_appmenu")
                        .should("exist")
                        .then(() => {
                            const menu_data = {
                                profile: profile,
                                menus: res.response.body.data.menus,
                            };
                            cy.compare_sessionStorage_profiles(menu_data);

                            cy.url().should("eq", Cypress.config("baseUrl"));

                            Cypress.env("test_menu_data", menu_data);
                        });
                });
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
});
// Accept: */*
// Accept-Encoding: gzip, deflate, br
// Accept-Language: en-US,en;q=0.9
// Content-Length: 2
// Content-Type: application/json
// Host: localhost:8069
// Origin: http://localhost:8069
// Proxy-Connection: keep-alive
// Referer: http://localhost:8069/shopfloor_mobile/app/
// sec-ch-ua: "Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"
// sec-ch-ua-mobile: ?0
// sec-ch-ua-platform: "Linux"
// Sec-Fetch-Dest: empty
// Sec-Fetch-Mode: cors
// Sec-Fetch-Site: same-origin
// SERVICE-CTX-PROFILE-ID: 1
// User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36
