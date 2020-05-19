export var PickingDetailMixin = {
    props: {
        // TODO: rename to `record`
        picking: Object,
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
                on_title_action: this.$props.options.clickable
                    ? this.on_title_action
                    : null,
            });
            return opts;
        },
    },
    template: `
  <item-detail-card :record="picking" :options="opts">
    <template v-slot:subtitle>
      <span class="origin" v-if="picking.origin">
          <span>{{ picking.origin }}</span>
      </span>
      <span v-if="picking.origin && picking.partner"> - </span>
      <span class="partner" v-if="picking.partner">
          <span>{{ picking.partner.name }}</span>
      </span>
    </template>
  </item-detail-card>
`,
};

Vue.component("detail-picking", {
    mixins: [PickingDetailMixin],
});
