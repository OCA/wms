export var PickingDetailMixin = {
    props: {
        // TODO: rename to `record`
        record: Object,
        options: Object,
        clickable: {
            type: Boolean,
            // TODO: this must be false when showing picking screen (eg: scan anything)
            default: true,
        },
    },
    methods: {
        on_title_action() {
            // TODO: we should probably delegate this to a global event
            this.$router.push({
                name: "scananything",
                params: {identifier: this.picking.name},
                query: {displayOnly: 1},
            });
        },
    },
    computed: {
        opts() {
            const opts = _.defaults({}, this.$props.options, {
                on_title_action: this.$props.clickable ? this.on_title_action : null,
            });
            return opts;
        },
    },
    template: `
  <item-detail-card :record="record" :options="opts">
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
