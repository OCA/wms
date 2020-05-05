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
    },
    template: `
<div v-if="!_.isEmpty(line)" :class="'detail batch-picking-line-detail ' + (line.postponed ? 'line-postponed' : '')">

  <item-detail-card :record="line" :options="{main: true, loud: true, no_title: true, fields: detail_fields()}" />

  <!-- TODO: replace this w/ detail card too -->
  <v-card outlined v-if="showFullInfo">
    <v-card-title>{{ line.product.default_code }}</v-card-title>
    <v-card-subtitle>{{ line.product.name }}</v-card-subtitle>

    <v-card-title>{{ line.picking.name }}</v-card-title>
    <v-card-subtitle>
      <div class="batch"><span class="label">From batch:</span> {{ line.batch.name }}</div>
    </v-card-subtitle>
    <v-card-text>
      <div class="ref" v-if="line.picking.origin">
        <span>{{ line.picking.origin }}</span>
      </div>
      <div class="customer" v-if="line.picking.partner">
        <span>{{ line.picking.partner.name }}</span>
      </div>
      <div class="qty-on-hand"><span class="label">On hand qty:</span> {{ line.product.qty_available }}</div>
      <div class="destination"><span class="label">Destination:</span> {{ line.location_dest.name }}</div>
    </v-card-text>
  </v-card>

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
    template: `
  <div class="batch-picking-line-actions">
    <v-dialog v-model="dialog" fullscreen tile class="actions fullscreen text-center">
      <template v-slot:activator="{ on }">
        <v-row class="actions bottom-actions">
          <v-col>
            <v-btn depressed color="primary" dark v-on="on">Action</v-btn>
          </v-col>
        </v-row>
      </template>
      <v-card>
        <div class="button-list button-vertical-list full">
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <v-btn depressed x-large color="primary" @click="$emit('action', 'action_full_bin')">Go to destination - full bin(s)</v-btn>
            </v-col>
          </v-row>
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <v-btn depressed x-large color="primary" @click="$emit('action', 'action_skip_line')">Skip line</v-btn>
            </v-col>
          </v-row>
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <v-btn depressed x-large color="primary"
                  @click="$emit('action', 'action_stock_out')">Declare stock out</v-btn>
            </v-col>
          </v-row>
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <v-btn depressed x-large color="primary" @click="$emit('action', 'action_change_pack_or_lot')">Change lot or pack [TODO]</v-btn>
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
        template: `
    <div class="batch-picking-line-stock-out">
      <batch-picking-line-detail :line="line" :showFullInfo="false" />
      <div class="button-list button-vertical-list full">
        <v-row align="center">
          <v-col class="text-center" cols="12">
            <v-btn depressed x-large color="primary" @click="$emit('action', 'confirm_stock_issue')">Confirm stock = 0</v-btn>
          </v-col>
        </v-row>
        <v-row align="center">
          <v-col class="text-center" cols="12">
            <v-btn depressed x-large color="default" @click="$emit('action', 'back')">back</v-btn>
          </v-col>
        </v-row>
      </div>
    </div>
`,
    }
);
