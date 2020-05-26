/* eslint-disable strict */
Vue.component("batch-picking-detail", {
    props: ["record"],
    methods: {
        detail_fields() {
            return [
                {path: "picking_count", label: "Total operations"},
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
  <div class="detail batch-picking-detail with-bottom-actions" v-if="!_.isEmpty(record)">

    <div class="review">

      <item-detail-card :record="record" :options="{main: true, loud: true, fields: detail_fields()}" />

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

    <div class="pickings">
      <separator-title>Pickings list</separator-title>
      <detail-picking
        v-for="picking in record.pickings"
        :key="picking.id"
        :record="picking"
        :options="{fields: picking_detail_fields()}"
        />
    </div>

</div>
`,
});
