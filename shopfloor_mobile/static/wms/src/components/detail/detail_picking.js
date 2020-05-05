export var PickingDetailMixin = {
    props: {
        // TODO: rename to `record`
        picking: Object,
        options: Object,
    },
    template: `
  <item-detail-card :record="picking" v-bind="$props">
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
