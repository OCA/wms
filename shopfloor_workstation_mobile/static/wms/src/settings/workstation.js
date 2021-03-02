/**
 * Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
 * @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {page_registry} from "/shopfloor_mobile_base/static/wms/src/services/page_registry.js";
import {config_registry} from "/shopfloor_mobile_base/static/wms/src/services/config_registry.js";
import {translation_registry} from "/shopfloor_mobile_base/static/wms/src/services/translation_registry.js";

var Workstation = {
    data: function() {
        return {
            usage: "workstation",
            workstation_scanned: false,
            scan_data: {},
            scan_message: {},
            search_input_placeholder: this.$t("screen.settings.workstation.scan"),
        };
    },
    template: `
        <Screen :screen_info="{title: $t('screen.settings.workstation.title'), klass: 'settings settings-workstation'}">
            <template v-slot:header>
                <user-information
                    v-if="workstation_scanned"
                    :message="scan_message"
                    />
            </template>
            <searchbar
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
                />

            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-back/>
                    </v-col>
                </v-row>
            </div>
        </Screen>
    `,
    mounted() {
        const odoo_params = {usage: this.usage};
        this.odoo = this.$root.getOdoo(odoo_params);
    },
    methods: {
        on_scan: function(scanned) {
            this.odoo.call("setdefault", {barcode: scanned.text}).then(result => {
                this.workstation_scanned = true;
                // TODO : See how well a 404 when the shopfloor_workstation
                // module is not installed will be handeled.
                // Maybe there will be some this.$root.appconfig.features.xyz
                // to test if installed.
                this.scan_data = result.data;
                this.scan_message = result.message;
                if (this.scan_data) {
                    this.$root.workstation = this.scan_data;
                    if (this.scan_data.profile) {
                        this.$root.trigger(
                            "profile:selected",
                            this.scan_data.profile,
                            true
                        );
                    }
                    // TODO: the success message will not be displayed, as we change screen !
                    this.$root.$router.push({name: "settings"});
                }
            });
        },
    },
};

// Register settings page
page_registry.add(
    "workstation",
    Workstation,
    {},
    {
        tag: "settings",
        icon: "mdi-printer",
        display_name: function(instance, rec) {
            const workstation_name = instance.$root.workstation
                ? instance.$root.workstation.name
                : "?";
            return [
                instance.$t("screen.settings.workstation.name"),
                workstation_name,
            ].join(" - ");
        },
    }
);

// Register global config property
config_registry.add("workstation", {default: {}, reset_on_clear: true});

// Add new translations
translation_registry.add("en-US.screen.settings.workstation", {
    name: "Workstation",
    title: "Select workstation",
    updated: "Workstation updated",
    scan: "Scan workstation",
});
translation_registry.add("fr-FR.screen.settings.workstation", {
    name: "Station de travail",
    title: "Choisissez une station de travail",
    updated: "Station de travail mise à jour",
    scan: "Scan station de travail",
});
// TODO
// translation_registry.add(
//     "de-DE.screen.settings.workstation", {
//         name: "Station de travail",
//         title: "Choisissez une station de travail",
//         updated: "Station de travail mise à jour",
//     },
// );

export default Workstation;
