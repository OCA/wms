describe("Test to make sure that handling different profiles works as expected", () => {
    // This test covers the access to the different profiles
    // of the application, their selection and how they display
    // their different scenarios.

    before(() => {
        sessionStorage.clear();
        cy.fixture("demo_profiles").then((profiles) => {
            Cypress.env("test_profiles", profiles);
        });
    });

    it("Goes to the list of profiles", () => {
        cy.visit(Cypress.config("baseUrlExampleDemo") + "profile");
    });
    it("Checks the demo profiles are displayed", () => {
        const profiles = Cypress.env("test_profiles");
        check_profile_list(profiles);
    });

    // i starts with 1 as that's the id of the first demo profile
    for (let i = 1; i <= 2; i++) {
        describe("Select profile", () => {
            it(`Selects profile ${i}`, () => {
                const profiles = Cypress.env("test_profiles");
                const profile = profiles[i - 1];
                cy.activate_profile(profile);
            });
        });
        describe("Profile tests", () => {
            describe("Test profile", () => {
                it("Checks the page is redirected and the local information was stored correctly", () => {
                    cy.url().should("eq", Cypress.config("baseUrlExampleDemo"));
                    const profiles = Cypress.env("test_profiles");
                    compare_sessionStorage_profile(profiles[i - 1]);
                });
                it("Goes back to the profile page", () => {
                    cy.sidebar_menu_to("settings");
                    cy.contains("Profile -", {matchCase: false}).click();
                });
            });
        });
    }
});

// Test-specific functions
const compare_sessionStorage_profile = (profile) => {
    cy.window().then((win) => {
        const stored_profile = JSON.parse(
            win.sessionStorage.getItem("shopfloor_profile")
        ).value;

        if (JSON.stringify(stored_profile) !== JSON.stringify(profile)) {
            throw new Error(
                "The profile information stored in the session storage doesn't match the response from the request"
            );
        }
    });
};

const check_profile_list = (profiles) => {
    profiles.forEach((profile) => {
        cy.contains(profile.name, {matchCase: false});
    });
};
