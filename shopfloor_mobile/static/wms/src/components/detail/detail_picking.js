/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

export var PickingDetailMixin = {
    props: {
        record: Object,
        options: Object,
    },
    computed: {
        opts() {
            const opts = _.defaults({}, this.$props.options, {
                title_action_field: {path: "name", action_val_path: "name"},
            });
            return opts;
        },
    },
    template: `
  <item-detail-card :record="record" :options="opts" v-bind="$attrs">
    <template v-slot:subtitle>
      <span class="origin" v-if="record.origin">
          <span>{{ record.origin }}</span>
      </span>
      <span v-if="record.origin && record.partner"> - </span>
      <span class="partner" v-if="record.partner">
          <span>{{ record.partner.name }}</span>
      </span>
    </template>
    <template v-slot:after_details>
        <slot name="actions"></slot>
    </template>
  </item-detail-card>
`,
};

Vue.component("detail-picking", {
    mixins: [PickingDetailMixin],
});
