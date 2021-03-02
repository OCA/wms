/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {utils_registry} from "./services/utils_registry.js";

export var GlobalMixin = {
    methods: {
        /*
        Try to make unique component keys.

        Includes tha parent key by default.
        */
        make_component_key: function(bits) {
            const parent_key = _.result(this.$parent, "$options._componentTag", "");
            if (parent_key) bits.unshift(parent_key + "-");
            bits.unshift(this.$options._componentTag);
            return bits.join("-");
        },
    },
    computed: {
        /*
        Provide utils to all components
        */
        utils: function() {
            return utils_registry.all();
        },
        available_languages() {
            return this.$root.available_languages;
        },
        active_language_code() {
            return this.$i18n.locale || "en-US";
        },
        active_language() {
            const language = this.available_languages.find(
                ({id}) => id === this.active_language_code
            );
            return language ? language.name : "?";
        },
    },
};
