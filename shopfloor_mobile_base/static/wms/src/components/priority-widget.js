/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

export var PriorityWidget = Vue.component("priority-widget", {
    props: {
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
    <span v-if="opts.label">{{ opts.label }}</span>
    <span v-for="n in _.range(1, opts.priority + 1)" v-if="opts.priority" :class="['priority-' + n]">
        <v-icon color="amber accent-2">mdi-star</v-icon>
    </span>
</div>
`,
});
