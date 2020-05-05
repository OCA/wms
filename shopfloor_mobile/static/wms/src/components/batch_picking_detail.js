/* eslint-disable strict */
Vue.component("batch-picking-detail", {
    props: ["info"],
    methods: {
        detail_fields() {
            return [
                {path: "move_line_count", label: "Lines"},
                {path: "weight", label: "Weight"},
            ];
        },
        picking_detail_fields() {
            return [
                {path: "move_line_count", label: "Lines"},
                {path: "weight", label: "Weight"},
            ];
        },
    },
    template: `
  <div class="detail batch-picking-detail with-bottom-actions" v-if="!_.isEmpty(info)">
    <div>

      <item-detail-card :record="info" :options="{main: true, fields: detail_fields()}">

        <template v-slot:title>
          Operations: {{ info.pickings.length }}
        </template>

        <template v-slot:subtitle>
          {{ info.name }}
        </template>

      </item-detail-card>

      <detail-picking
        v-for="picking in info.pickings"
        :key="picking.id"
        :picking="picking"
        :klass="'listed'"
        :options="{fields: picking_detail_fields()}"
        />

    </div>
    <v-row class="actions bottom-actions">
      <v-col>
        <v-btn depressed color="primary" @click="$emit('confirm')">Start</v-btn>
      </v-col>
      <v-col>
        <v-btn depressed color="error" class="float-right" @click="$emit('cancel')">Cancel</v-btn>
      </v-col>
    </v-row>

</div>
`,
});
