
var batch_picking_info = Vue.component('batch-picking-detail', {
  props:['info'],
  template: `
  <div class="detail batch-picking-detail" v-if="!_.isEmpty(info)">
    <v-card class="mb-2">
      <v-card-title>Work package info</v-card-title>
      <v-card-text>
        <ul>
          <li>Operations: {{ info.picking_count }}</li>
          <li>Lines: {{ info.move_line_count }}</li>
          <li>Total weight: [TODO]</li>
        </ul>
      </v-card-text>
    </v-card>

    <v-card v-for="rec in info.records">
      <v-card-title> {{ rec.name }} </v-card-title>
      <v-card-text>
        <ul>
          <li>Customer: {{ rec.customer.name }}</li>
          <li>Lines: {{ rec.move_line_count }}</li>
          <li>Weight: [TODO]</li>
          <li>REF: {{ info.ref }}</li>
        </ul>
      </v-card-text>
    </v-card>

    <v-btn color="primary" @click="$emit('confirm')">Start</v-btn>
    <v-btn color="error" @click="$emit('cancel')">Cancel</v-btn>

</div>
`
})
