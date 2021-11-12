describe("Test to make sure that handling different profiles works as expected", () => {
    // This test covers module shopfloor_example, which provides
    // an example scenario "Manage partners" in profile "Partner manager".
    // It tests that it can be accessed and that the partners can be
    // selected both manually and through ref scan.

    before(() => {
        cy.prepare_test_authentication();
    });

    beforeEach(() => {
        Cypress.Cookies.preserveOnce("session_id");
    });

    describe("Selects example profile 'Partner manager'", () => {
        it("Navigates to the profile list and selects the profile", () => {
            const credentials = Cypress.env("credentials");
            // Logs in
            cy.intercept_user_config_request();
            cy.login(credentials);
            cy.wait_for({expect_success: true, request_name: "user_config"}).then(
                (res) => {
                    // Goes to the profile page and checks the list of profiles
                    cy.url().should("eq", Cypress.config("baseUrl"));
                    cy.get(".profile-not-ready").find("button").click();
                    cy.contains("Profile -", {matchCase: false}).click();

                    // Clicks on 'Partner manager'
                    const profiles = res.response.body.data.profiles;
                    const profile = profiles.filter(
                        (profile) => profile.name === "Partner manager"
                    )[0];

                    cy.activate_profile(profile);
                }
            );
        });
        it("Opens the example scenario", () => {
            open_scenario("partner_example");
            cy.url().should("include", "partner_example");
        });
    });
    describe("Tests manual selection", () => {
        it("Selects a partner manually", () => {
            intercept_partner_list_request();
            cy.contains("manual selection", {matchCase: false}).click();

            cy.wait_for({expect_success: true, request_name: "partner_list"}).then(
                (res) => {
                    const partners = res.response.body.data.listing.records;
                    Cypress.env("test_partners", partners);

                    check_page_contains_partners(partners);

                    const first_partner_id = partners[0].id;
                    intercept_single_partner_detail_request();
                    cy.get(`input[value=${first_partner_id}]`).click();
                }
            );
            cy.wait_for({
                expect_success: true,
                request_name: "single_partner_detail",
            }).then((res) => {
                const record = res.response.body.data.detail.record;
                Cypress.env("test_current_partner", record);
            });
        });
        it("Checks that the partner was correctly selected", () => {
            test_partner_card();
        });
    });
    describe("Tests scan selection", () => {
        it("Selects a partner by scan ref", () => {
            scan_partner(26);
        });
        it("Checks that the partner was correctly selected", () => {
            test_partner_card();
        });
    });
});

// Test-specific functions

const open_scenario = (scenario_name) => {
    cy.get("a").contains(scenario_name).click();
    cy.url().should("include", Cypress.config("baseUrl") + scenario_name);
    cy.get("button").contains("manual selection", {matchCase: false});
};

const check_page_contains_partners = (partners) => {
    partners.forEach((partner) => {
        cy.contains(partner.name, {matchCase: false});
    });
};

const scan_partner = (id) => {
    intercept_partner_scan_request();
    cy.get("input").type(id);
    cy.get("form").submit();
    cy.wait_for({expect_success: true, request_name: "partner_scan"}).then((res) => {
        const record = res.response.body.data.detail.record;
        Cypress.env("test_current_partner", record);
    });
};

const test_partner_card = () => {
    const record = Cypress.env("test_current_partner");
    cy.get(".detail-partner_example").contains(record.name);
    cy.get(".detail-partner_example").contains(`Ref: ${record.id}`);
    cy.get(".detail-partner_example").contains(`Email: ${record.email}`);
};

const intercept_partner_list_request = () => {
    cy.intercept({
        method: "GET",
        url: "*/partner_example/partner_list*",
    }).as("partner_list");
};

const intercept_partner_scan_request = () => {
    cy.intercept({
        method: "GET",
        url: "*/partner_example/scan/*",
    }).as("partner_scan");
};

const intercept_single_partner_detail_request = () => {
    cy.intercept({
        method: "GET",
        url: "*/partner_example/detail/*",
    }).as("single_partner_detail");
};
