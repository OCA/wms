export var PriorityWidget = Vue.component("priority-widget", {
    props: {
        record: Object,
        options: Object,
    },
    computed: {
        opts() {
            const opts = _.defaults({}, this.$props.options, {
                mode: "",
            });
            return opts;
        },
    },
    template: `
<div :class="[$options._componentTag, opts.mode ? 'mode-' + opts.mode: '', 'd-inline']">
    <span v-for="n in _.range(1, opts.priority + 1)" v-if="opts.priority" :class="['priority-' + n]">
        <v-icon color="amber accent-2">mdi-star</v-icon>
    </span>
</div>
`,
});
