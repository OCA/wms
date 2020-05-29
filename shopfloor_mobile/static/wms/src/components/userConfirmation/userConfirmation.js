Vue.component("user-confirmation", {
    props: ["title", "question"],
    methods: {},
    template: `

    <div class="confirm">
        <v-alert type="warning" prominent tile>
            <p class="warning darken-2 title pa-5 mt-5">{{ question }}</p>
            <v-form class="mt-4">
                <div class="button-list button-vertical-list full">
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
                </div>
            </v-form>
        </v-alert>
    </div>

`,
});
