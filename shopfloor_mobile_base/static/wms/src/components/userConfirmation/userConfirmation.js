/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
Vue.component("user-confirmation", {
    props: ["title", "question"],
    methods: {},
    template: `

    <div class="confirm">
        <v-card tile>
            <v-card-title>{{title}}</v-card-title>
            <v-card-text>
                <v-alert type="warning" prominent tile>{{ question }}</v-alert>
            </v-card-text>
            <v-form class="mt-4">
                <v-container class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action @click="$emit('user-confirmation', 'yes')">Yes</btn-action>
                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <btn-action action="cancel" @click="$emit('user-confirmation', 'no')">No</btn-action>
                        </v-col>
                    </v-row>
                </v-container>
            </v-form>
        </v-card>
    </div>

`,
});
