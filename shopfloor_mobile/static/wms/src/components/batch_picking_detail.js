export var batch_picking_info = Vue.component('batch-picking-detail', {
    props:['info'],
    template: `
  <div class="detail batch-picking-detail with-bottom-actions" v-if="!_.isEmpty(info)">
    <div>
      <v-card outlined class="main">
        <v-card-title>Operations: {{ info.pickings.length }}</v-card-title>
        <v-card-subtitle>{{ info.name }}</v-card-subtitle>
        <v-card-text>
          <div class="lines-nr">
            <span class="label">Lines:</span>
            {{ _.sumBy(info.pickings, function(p) { return p.move_line_count; }) }}
          </div>
          <div class="weight">
            <span class="label">Weight:</span>
            {{ _.sumBy(info.pickings, function(p) { return p.weight; }) }}
          </div>
        </v-card-text>
      </v-card>

      <v-card outlined v-for="rec in info.pickings" :key="rec.id">
        <v-card-title> {{ rec.name }} </v-card-title>
        <v-card-text>
          <div class="lines-nr">
            <span class="label">Lines:</span>
            {{ _.sumBy(info.pickings, function(p) { return p.move_line_count; }) }}
          </div>
          <div class="weight">
            <span class="label">Weight:</span>
            {{ _.sumBy(info.pickings, function(p) { return p.weight; }) }}
          </div>
          <div class="partner" v-if="rec.partner">
            <span class="label">Customer:</span> {{ rec.partner.name }}
          </div>
          <div class="origin" v-if="rec.origin">
            <span class="label">REF:</span> {{ rec.origin }}
          </div>
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
`,
});
