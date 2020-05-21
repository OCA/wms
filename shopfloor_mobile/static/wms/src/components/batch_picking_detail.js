/* eslint-disable strict */
Vue.component("batch-picking-detail", {
    props: ["info"],
    methods: {
        detail_fields() {
            return [
                {path: "move_line_count", label: "Total lines"},
                {path: "weight", label: "Total weight"},
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

      <item-detail-card :record="info" :options="{main: true, loud: true, fields: detail_fields()}">

        <template v-slot:title>
          Total operations: {{ info.picking_count }}
        </template>

        <template v-slot:subtitle>
          {{ info.name }}
        </template>

      </item-detail-card>

      <separator-title>Pickings</separator-title>

      <detail-picking
        v-for="picking in info.pickings"
        :key="picking.id"
        :picking="picking"
        :klass="'listed'"
        :options="{fields: picking_detail_fields()}"
        />

    </div>
    <div class="button-list button-vertical-list full">
      <v-row align="center">
        <v-col class="text-center" cols="12">
          <v-btn color="primary" @click="$emit('confirm')">Start</v-btn>
        </v-col>
      </v-row>
      <v-row align="center">
        <v-col class="text-center" cols="12">
          <v-btn color="error" @click="$emit('cancel')">Cancel</v-btn>
        </v-col>
      </v-row>
    </div>
</div>
`,
});
