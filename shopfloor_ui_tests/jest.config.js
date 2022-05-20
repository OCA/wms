const lodash = require("lodash");
const Vue = require("vue");
const Vuetify = require("vuetify");

Vue.use(Vuetify);

module.exports = {
    preset: "@vue/cli-plugin-unit-jest",
    transformIgnorePatterns: ["/node_modules/(?!ol)"],
    testMatch: ["**/__unit_tests__/**/*.[jt]s?(x)", "**/?(*.)+(spec|test).[jt]s?(x)"],
    globals: {
        _: lodash,
        Vue,
        Vuetify,
    },
    modulePaths: [
        "<rootDir>", // shopfloor_ui_tests
        "<rootDir>/../", // wms
    ],
};
