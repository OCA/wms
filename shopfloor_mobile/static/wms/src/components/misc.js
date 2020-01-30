Vue.component('reset-screen-button', {
    props: ['show_reset_button'],
    methods: {
        reset: function () {
		    this.$emit('reset')
        }
    },
    template: `
    <v-form class="mt-5" v-if="show_reset_button" v-on:reset="reset">
        <v-btn @click="reset">Reset</v-btn>
    </v-form>
    `,
})
