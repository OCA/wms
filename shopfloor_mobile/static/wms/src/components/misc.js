Vue.component('reset-screen-button', {
    props: ['show_reset_button'],
    methods: {
        reset: function () {
		    this.$emit('reset')
        }
    },
    template: `
    <v-form class="mt-5" v-if="show_reset_button" v-on:reset="reset">
        <v-btn depressed @click="reset">Reset</v-btn>
    </v-form>
    `,
})


// TODO: could be merged w/ userConfirmation
Vue.component('last-operation', {
    // props: ['info'],
    data: function () {
        return {'info': {
            'last_operation_name': 'Last operation XYZ',
            'next_operation_name': 'Next operation XYZ',
        }}
    },
    // methods: {
    //     on_submit: function () {
	// 	    this.$emit('confirm')
    //     }
    // },
    template: `
    <div class="last-operation">
        <v-dialog persistent fullscreen tile value=true>
            <v-alert type="info" prominent transition="scale-transition">
                <v-card outlined color="blue lighten-1" class="message mt-10">
                    <v-card-title>Last operation of the document</v-card-title>
                    <v-card-text>{{info.last_operation_name}}</v-card-text>
                </v-card>
                <v-card outlined color="blue lighten-1" class="message mt-10">
                    <v-card-title>Next operation ready to be processed</v-card-title>
                    <v-card-text>{{info.next_operation_name}}</v-card-text>
                </v-card>
                <v-form class="mt-10">
                    <v-btn x-large color="success" @click="$emit('confirm')">OK</v-btn>
                </v-form>
            </v-alert>
        </v-dialog>
    </div>
    `,
})
