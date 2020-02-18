export var NumberSpinner = Vue.component('input-number-spinner', {
    template: `

<div class="number-spinner">
    <div class="spinner-btn plus" v-on:click="increase()">
        <slot name="plus"><span>+</span></slot>
    </div>
    <div class="input-wrapper">
        <input :type="input_type" v-model="value" disabled />
    </div>
    <div class="spinner-btn minus" v-on:click="decrease()">
        <slot name="minus"><span>-</span></slot>
    </div>
</div>
`,
    props: {
        input_type: {
            default: 'text',  // avoid default browser spinner
            type: String
        },
        init_value: {
            default: 0,
            type: Number
        },
        min: {
            default: 0,
            type: Number
        },
        max: {
            default: undefined,
            type: Number
        },
        step: {
            default: 1,
            type: Number
        }

    },
    data: function () {
        return {
            value: 0
        }

    },
    methods: {
        increase: function() {
            if(this.max == undefined || (this.value < this.max)) {
                this.value = this.value + this.step
                this.$emit('input', this.value)
            }
        },
        decrease: function() {
            if((this.value) > this.min) {
                let new_val = this.value - this.step
                this.value = new_val >= this.min ? new_val : this.min
                this.$emit('input', this.value)
            }
        }
    },
    watch: {
        value: {
            handler: function (newVal, oldVal) {
                this.value = newVal
            }
        }
    },
    created: function() {
        this.value = this.init_value
    }
})
