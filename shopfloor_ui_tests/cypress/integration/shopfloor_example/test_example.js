describe("Test to make sure that handling different profiles works as expected", () => {
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
                    cy.get(".text-center").children("button").click();
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
            cy.open_scenario("partner_example");
            cy.url().should("include", "partner_example");
        });
    });
    describe("Tests manual selection", () => {
        it("Selects a partner manually", () => {
            cy.intercept_partner_list_request();
            cy.contains("manual selection", {matchCase: false}).click();

            cy.wait_for({expect_success: true, request_name: "partner_list"}).then(
                (res) => {
                    const partners = res.response.body.data.listing.records;
                    Cypress.env("test_partners", partners);

                    cy.check_page_contains_partners(partners);

                    const first_partner_id = partners[0].id;
                    cy.intercept_single_partner_detail_request();
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
            cy.test_partner_card();
        });
    });
    describe("Tests scan selection", () => {
        it("Selects a partner by scan ref", () => {
            cy.scan_partner(26);
        });
        it("Checks that the partner was correctly selected", () => {
            cy.test_partner_card();
        });
    });
});
