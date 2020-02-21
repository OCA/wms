export var batch_picking_line = Vue.component('batch-picking-line-detail', {
  props: {
      'line': Object,
      'showFullInfo': {
          'type': Boolean,
          'default': true,
      },
  },
  data () {
    return {
      dialog: false,
    }
  },
  template: `
  <div class="detail batch-picking-line-detail" v-if="!_.isEmpty(line)">
    <v-card outlined class="main">
      <v-card-title>{{ line.picking.name }}</v-card-title>
      <v-card-subtitle>
        From batch <strong>{{ line.batch.name }}</strong>
      </v-card-subtitle>
      <v-card-text>
        <div v-if="line.picking.origin"><span class="ref">{{ line.picking.origin }}</span> - <span class="ref">[CUSTOMER TODO]</span></div>
        <div><span class="source">{{ line.location_src.name }}</span></div>
      </v-card-text>
    </v-card>

    <v-card outlined v-if="showFullInfo">
      <v-card-title>{{ line.product.display_name }}</v-card-title>
      <v-card-text>
        <ul>
          <li><span class="pack">{{ line.pack.name }}</span></li>
          <li v-if="line.lot"><span class="lot">Lot: {{ line.lot.name }}</span></li>
          <li><span class="qty-on-hand">On-hand qty {{ line.product.qty_available }}</span></li>
          <li><span class="qty">Pkg qty [TODO]</span></li>
          <li><span class="bin">Destination bin {{ line.location_dst.name }}</span></li>
        </ul>
      </v-card-text>
    </v-card>

</div>
`
})


export var batch_picking_line_actions = Vue.component('batch-picking-line-actions', {
  props:['line'],
  data () {
    return {
      dialog: false,
    }
  },
  template: `
  <div class="batch-picking-line-actions">
    <v-dialog v-model="dialog" fullscreen tile class="actions fullscreen text-center">
      <template v-slot:activator="{ on }">
        <v-row class="actions bottom-actions">
          <v-col>
            <v-btn color="primary" dark v-on="on">Action</v-btn>
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
`
})


export var batch_picking_line_stock_out = Vue.component('batch-picking-line-stock-out', {
  props:['line'],
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
`
})