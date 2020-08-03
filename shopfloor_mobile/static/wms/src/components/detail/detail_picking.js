export var PickingDetailMixin = {
    props: {
        // TODO: rename to `record`
        record: Object,
        options: Object,
        // clickable: {
        //     type: Boolean,
        //     // TODO: this must be false when showing record screen (eg: scan anything)
        //     default: true,
        // },
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
  </item-detail-card>
`,
};

Vue.component("detail-picking", {
    mixins: [PickingDetailMixin],
});
