export var batch_picking_info = Vue.component('batch-picking-detail', {
  props:['info'],
  template: `
  <div class="detail batch-picking-detail with-bottom-actions" v-if="!_.isEmpty(info)">
    <div>
      <v-card outlined class="main">
        <v-card-title>{{ info.name }}</v-card-title>
        <v-card-text>
          <ul>
            <li>Operations: {{ info.pickings.length }}</li>
            <li>Lines: {{ _.sumBy(info.pickings, function(p) { return p.move_line_count; }) }}</li>
            <li>Total weight: {{ _.sumBy(info.pickings, function(p) { return p.weight; }) }}</li>
          </ul>
        </v-card-text>
      </v-card>

      <v-card outlined v-for="rec in info.pickings" :key="rec.id">
        <v-card-title> {{ rec.name }} </v-card-title>
        <v-card-text>
          <ul>
            <li v-if="rec.partner">{{ rec.partner.name }}</li>
            <li>Lines: {{ rec.move_line_count }}</li>
            <li>Weight: {{ rec.weight }}</li>
            <li v-if="rec.origin">REF: {{ rec.origin }}</li>
          </ul>
        </v-card-text>
      </v-card>

    </div>
    <v-row class="actions bottom-actions">
      <v-col>
        <v-btn color="primary" @click="$emit('confirm')">Start</v-btn>
      </v-col>
      <v-col>
        <v-btn color="error" class="float-right" @click="$emit('cancel')">Cancel</v-btn>
      </v-col>
    </v-row>

</div>
`
})
