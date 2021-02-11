/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "../services/process_registry.js";

const Form = {
    template: `
        <Screen :screen_info="screen_info">
            <component
                :is="form_component_name()"
                :record="record"
                :form="form"
                v-on:change="on_change"
                />
            <div class="button-list button-vertical-list full" v-if="!_.isEmpty(record)">
                <v-row align="center">
                    <v-col class="text-center">
                        <btn-back />
                    </v-col>
                </v-row>
            </div>
        </Screen>
    `,
    data: function() {
        return {
            usage: "",
            form_name: "",
            record: {},
            form: {},
            user_message: {},
        };
    },
    mounted: function() {
        this.usage = this.$route.params.form_name;
        const odoo_params = {
            usage: this.usage,
            profile_id: this.$root.profile.id,
        };
        this.odoo = this.$root.getOdoo(odoo_params);
        if (this.$route.params.record_id) {
            this._getFormData(this.$route.params.record_id);
        }
    },
    methods: {
        on_change: function(form_data) {
            if (!form_data.changed) {
                return;
            }
            const self = this;
            let form_values = form_data.values;
            this.odoo
                .call(this.record.id + "/update", form_values)
                .then(function(result) {
                    self._load_form_data(result);
                    /**
                     * TODO: dirty hack to be able to display the message to the user
                     * and redirect right after to former page.
                     * Ideally we should bubble up the event and the message
                     * to the parent component, but this should be made configurable
                     * by form as you might want to stay in the same place on save.
                     *  */

                    setTimeout(function() {
                        self.$root.trigger("go_back");
                        self.$router.back();
                    }, 1500);
                });
        },
        _getFormData: function(record_id) {
            this.odoo.call(record_id, {}, "GET").then(this._load_form_data);
        },
        _load_form_data: function(result) {
            this.odoo_data = result.data || {};
            this.record = this.odoo_data.record || {};
            this.form = this.odoo_data.form || {};
            this.user_message = result.message || null;
        },
        form_component_name() {
            if (_.isEmpty(this.form)) {
                return null;
            }
            const name = this.usage.split("_").join("-");
            // FIXME: this check does not work
            if (!name in Vue.options.components) {
                console.error("Form component ", name, " not found.");
                return null;
            }
            return name;
        },
    },
    computed: {
        screen_info: function() {
            return {
                title: this.screen_title,
                klass: "form",
                user_message: this.user_message,
            };
        },
        screen_title: function() {
            let title = "Edit"; // TODO: this should come from the form
            if (!_.isEmpty(this.record)) {
                title = "Edit: " + this.record.name;
            }
            return title;
        },
    },
};

process_registry.add("edit_form", Form, {
    path: "/form/:form_name/:record_id?",
});

export default Form;
