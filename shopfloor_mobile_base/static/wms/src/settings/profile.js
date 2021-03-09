/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {page_registry} from "../services/page_registry.js";

export var Profile = {
    data: function() {
        return {
            current_profile_id: this.$root.has_profile ? this.$root.profile.id : null,
            profile_selected: false,
            user_notif_updated: {
                body: this.$t("screen.settings.profile.profile_updated"),
                message_type: "info",
            },
        };
    },
    template: `
        <Screen :screen_info="{title: $t('screen.settings.profile.title'), klass: 'settings settings-profile'}">
            <template v-slot:header>
                <!-- TODO: rely on global notification -->
                <user-information
                    v-if="profile_selected"
                    :message="user_notif_updated"
                    />
            </template>
            <manual-select
                :records="$root.profiles"
                :options="{initValue: current_profile_id, showActions: false, required: true}"
                v-on:select="on_select"
                />

            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-back/>
                    </v-col>
                </v-row>
                <!-- FIXME: maybe not a good place here -->
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-reset-config />
                    </v-col>
                </v-row>
            </div>
        </Screen>
    `,
    methods: {
        on_select: function(selected) {
            if (!_.isEmpty(selected)) {
                this.$root.trigger("profile:selected", selected, true);
                this.$root.$router.push({name: "home"});
            }
        },
    },
};

page_registry.add(
    "profile",
    Profile,
    {},
    {
        tag: "settings",
        icon: "mdi-account-cog",
        display_name: function(instance, rec) {
            const profile_name = instance.$root.has_profile
                ? instance.$root.profile.name
                : "?";
            return [instance.$t("screen.settings.profile.name"), profile_name].join(
                " - "
            );
        },
    }
);

export default Profile;
