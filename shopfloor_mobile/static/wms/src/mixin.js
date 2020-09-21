/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {utils} from "./utils.js";
import {color_registry} from "./services/color_registry.js";
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
            return {
                misc: utils,
                colors: color_registry,
            };
        },
    },
};
