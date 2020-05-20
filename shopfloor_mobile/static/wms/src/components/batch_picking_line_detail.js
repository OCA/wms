export var batch_picking_line = Vue.component("batch-picking-line-detail", {
    props: {
        line: Object,
        showFullInfo: {
            type: Boolean,
            default: true,
        },
    },
    data() {
        return {
            dialog: false,
        };
    },
    methods: {
        detail_fields() {
            return [
                {path: "location_src.name", label: "Location"},
                {path: "package_dest.name", label: "Destination"},
                {path: "package_src.name", label: "Pack"},
                {path: "quantity", label: "Qty"},
            ];
        },
        full_detail_fields() {
            return [
                {path: "product.default_code"},
                {path: "product.name"},
                {path: "picking.name"},
                {path: "batch.name"},
                {path: "picking.origin", label: "Origin"},
                {path: "picking.partner.name", label: "Customer"},
                {path: "product.qty_available", label: "Qty on hand"},
                {path: "location_dest.name", label: "Destination"},
            ];
        },
    },
    template: `
<div v-if="!_.isEmpty(line)" :class="'detail batch-picking-line-detail ' + (line.postponed ? 'line-postponed' : '')">

  <item-detail-card
    :key="'batch-picking-line-detail-1'"
    :record="line"
    :options="{main: true, loud: true, no_title: true, fields: detail_fields()}"
    />
  <item-detail-card
    v-if="showFullInfo"
    :key="'batch-picking-line-detail-2'"
    :record="line"
    :options="{no_title: true, loud_labels: true, fields: full_detail_fields()}"
    />

</div>
`,
});

export var batch_picking_line_actions = Vue.component("batch-picking-line-actions", {
    props: ["line"],
    data() {
        return {
            dialog: false,
        };
    },
    methods: {
        handle_action(action) {
            this.$emit("action", action);
            this.dialog = false;
        },
    },
    template: `
  <div class="batch-picking-line-actions">
    <v-dialog v-model="dialog" fullscreen tile class="actions fullscreen text-center">
      <template v-slot:activator="{ on }">
        <div class="button-list button-vertical-list full">
          <v-row class="actions bottom-actions">
            <v-col class="text-center" cols="12">
              <v-btn depressed color="primary" dark v-on="on">Action</v-btn>
            </v-col>
          </v-row>
        </div>
      </template>
      <v-card>
        <div class="button-list button-vertical-list full">
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <v-btn depressed x-large color="primary" @click="handle_action('action_full_bin')">Go to destination - full bin(s)</v-btn>
            </v-col>
          </v-row>
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <v-btn depressed x-large color="primary" @click="handle_action('action_skip_line')">Skip line</v-btn>
            </v-col>
          </v-row>
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <v-btn depressed x-large color="primary"
                  @click="handle_action('action_stock_out')">Declare stock out</v-btn>
            </v-col>
          </v-row>
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <v-btn depressed x-large color="primary" @click="handle_action('action_change_pack_or_lot')">Change lot or pack</v-btn>
            </v-col>
          </v-row>
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <v-btn depressed x-large color="secondary" @click="dialog = false">Back</v-btn>
            </v-col>
          </v-row>
        </div>
      </v-card>
    </v-dialog>
  </div>
`,
});

export var batch_picking_line_stock_out = Vue.component(
    "batch-picking-line-stock-out",
    {
        props: ["line"],
        methods: {
            handle_action(action) {
                this.$emit("action", action);
            },
        },
        template: `
    <div class="batch-picking-line-stock-out">
      <batch-picking-line-detail :line="line" :showFullInfo="false" />
      <div class="button-list button-vertical-list full">
        <v-row align="center">
          <v-col class="text-center" cols="12">
            <v-btn depressed x-large color="primary" @click="handle_action('confirm_stock_issue')">Confirm stock = 0</v-btn>
          </v-col>
        </v-row>
        <v-row align="center">
          <v-col class="text-center" cols="12">
            <v-btn depressed x-large color="default" @click="handle_action('back')">back</v-btn>
          </v-col>
        </v-row>
      </div>
    </div>
`,
    }
);
