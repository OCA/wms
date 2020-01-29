var userInformation = Vue.component('user-information', {
    props: ['info'],
    methods: {},
    template: `

    <v-alert :type="alert_type">
    {{ info.message }}
    </v-alert>
    `,
    computed: {
        alert_type: function () {
            return this.info.message_type
        }
    },

})
