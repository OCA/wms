var userInformation = Vue.component('user-information', {
    props: ['info'],
    methods: {},
    template: `

    <div v-bind:class="alert_class" role="alert">
        <p>{{ info.message }}</p>
    </div>
    `,
    computed: {
        alert_class: function () {
            // TODO: make this mapping configurable
            let mapping = {
                'default': 'alert-info',
                'info': 'alert-info',
                'error': 'alert-danger',
            }
            _class = mapping['default'];
            if (this.info.message_type in mapping)
                _class = mapping[this.info.message_type]
            return 'alert ' + _class
        }
    },

})
