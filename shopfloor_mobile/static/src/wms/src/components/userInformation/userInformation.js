var userInformation = Vue.component('user-information', {
    props: ['message', 'message_type'],
    methods: {},
    template: `

    <div v-bind:class="class_alert_type" role="alert">
        <p>{{ message }}</p>
    </div>

    `,
    computed: {
        class_alert_type: function () {
            return 'alert alert-' + (this.message_type || 'silent')
        }
    },

})
