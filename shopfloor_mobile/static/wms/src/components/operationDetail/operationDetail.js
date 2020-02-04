
var operationDetail = Vue.component('operation-detail', {
  data: function () {
    return {
        show_detail_dialog: false,
    }
  },
  props:['operation'],
    methods: {
        show_details: function() {
            this.show_detail_dialog = true;
        },
    },
  template: `
  <div class="detail operation-detail" v-if="!_.isEmpty(operation)">
    <v-simple-table>
    <template v-slot:default>
      <tbody>
      <tr class="teal lighten-2" v-if="operation.name">
        <th>Name</th>
        <td>
            {{ operation.name }}
            <v-btn @click="show_details" icon text class="float-right">
                <v-icon large dark>mdi-help-circle</v-icon>
            </v-btn>
        </td>
      </tr>
      <tr class="teal lighten-2" v-if="operation.barcode">
        <th>Barcode</th>
        <td>{{ operation.barcode }}</td>
      </tr>
      <tr class="teal lighten-2">
        <th>Source</th>
        <td>{{ operation.location_src.name }}</td>
      </tr>
      <tr class="amber">
        <th>Destination</th>
        <td>{{ operation.location_dst.name }}</td>
      </tr>
      </tbody>

    <v-dialog v-model="show_detail_dialog">
        <v-card>
            <detail-pack :packDetail="operation"></detail-pack>
            <v-card-actions>
                <v-btn color="primary" @click="show_detail_dialog = false">Close</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    </template>
  </v-simple-table>
</div>
`
})
