var userConfirmation = Vue.component('user-confirmation', {
    props: ['title', 'question'],
    methods: {},
    template: `

    <div class="confirm mt-4">
        <v-alert type="warning" prominent>
            {{ question }}
            <v-form class="mt-4">
                <v-btn
                    color="success"
                    type="submit"
                    value="yes"
                    @click="$emit('user-confirmation', 'yes')">Yes</v-btn>

                <v-btn
                    class="float-right"
                    color="error"
                    type="reset"
                    value="no"
                    @click="$emit('user-confirmation', 'no')">No</v-btn>
            </v-form>
        </v-alert>
    </div>

`,
});
