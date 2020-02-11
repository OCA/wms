Vue.component('reset-screen-button', {
    props: ['show_reset_button'],
    methods: {
        reset: function () {
		    this.$emit('reset')
        }
    },
    template: `
        <div class="action reset">
            <v-form class="m-t5" v-if="show_reset_button" v-on:reset="reset">
                <v-btn depressed x-large @click="reset">Reset</v-btn>
            </v-form>
        </div>
    `,
})

Vue.component('cancel-button', {
    template: `
        <div class="action reset">
            <v-btn depressed x-large color="error" v-on:click="$emit('cancel')">Cancel</v-btn>
        </div>
    `,
})

// TODO: could be merged w/ userConfirmation
Vue.component('last-operation', {
    // props: ['info'],
    data: function () {
        return {'info': {}}
    },
    template: `
    <div class="last-operation">
        <v-dialog persistent fullscreen tile value=true>
            <v-alert type="info" prominent transition="scale-transition">
                <v-card outlined color="blue lighten-1" class="message mt-10">
                    <v-card-title>This was the last operation of the document.</v-card-title>
                    <v-card-text>The next operation is ready to be processed.</v-card-text>
                </v-card>
                <v-form class="mt-10">
                    <v-btn x-large color="success" @click="$emit('confirm')">OK</v-btn>
                </v-form>
            </v-alert>
        </v-dialog>
    </div>
    `,
})


Vue.component('get-work', {
    template: `
    <div class="get-work">
        <v-btn id="btn-get-work" x-large color="success" @click="$emit('get_work')">
            Get work
        </v-btn>
        <v-btn id="btn-manual" color="default" @click="$emit('manual_selection')">
            Manual selection
        </v-btn>
    </div>
    `,
})

