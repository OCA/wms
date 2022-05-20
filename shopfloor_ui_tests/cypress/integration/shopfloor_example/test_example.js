describe("Test to make sure that handling different profiles works as expected", () => {
    // This test covers module shopfloor_example, which provides
    // an example scenario "Manage partners" in profile "Partner manager".
    // It tests that it can be accessed and that the partners can be
    // selected both manually and through ref scan.

    describe("Selects example profile 'Partner management (demo)'", () => {
        it("Navigates to the profile list and selects the profile", () => {
            cy.visit(Cypress.config("baseUrlExampleDemo"));
            cy.get(".profile-not-ready").find("button").click();
            cy.contains("Profile -", {matchCase: false}).click();
            cy.get("input[value=1]").parent().click();
        });
        it("Opens the example scenario", () => {
            open_scenario("partner_example");
            cy.url().should("include", "partner_example");
        });
    });
    describe("Tests manual selection", () => {
        it("Selects partners manually and checks the test partners are displayed correctly", () => {
            cy.contains("manual selection", {matchCase: false}).click();
            cy.fixture("example_partners").then((partners) => {
                Cypress.env("test_partners", partners);
                check_page_contains_partners(partners);
            });
        });
        it("Checks that the partners detail data is correct", () => {
            const partners = Cypress.env("test_partners");
            partners.forEach((partner) => {
                cy.get(`input[value=${partner.id}]`).click();
                test_partner_card(partner);
                cy.get(".v-btn--contained").first().click();
            });
        });
    });
    describe("Tests scan selection", () => {
        it("Selects a partner by scan ref and checks the data is correct", () => {
            cy.get(".v-btn--contained").first().click();
            const partners = Cypress.env("test_partners");
            partners.forEach((partner) => {
                scan_partner(partner.ref);
                test_partner_card(partner);
            });
        });
    });
});

// Test-specific functions
const open_scenario = (scenario_name) => {
    cy.get("a").contains(scenario_name).click();
    cy.url().should("include", Cypress.config("baseUrlExampleDemo") + scenario_name);
    cy.get("button").contains("manual selection", {matchCase: false});
};

const check_page_contains_partners = (partners) => {
    partners.forEach((partner) => {
        cy.contains(partner.name, {matchCase: false});
    });
};

const scan_partner = (ref) => {
    cy.get("input").type(ref);
    cy.get("form").submit();
};

const test_partner_card = (partner) => {
    cy.get(".detail-partner_example").contains(partner.name);
    cy.get(".detail-partner_example").contains(`Ref: ${partner.id}`);
    if (partner.email) {
        // Note: demo data only assigns emails
        // to partners with odd id, to simulate
        // blank email fields.
        cy.get(".detail-partner_example").contains(`Email: ${partner.email}`);
    } else {
        cy.get(".detail-partner_example").should("not.contain", "Email");
    }
};
