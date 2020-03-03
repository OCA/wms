
var operationDetail = Vue.component('operation-detail', {
    data: function () {
        return {
            show_popup_dialog: false,
            barcodeOpen: '',
        };
    },
    props:['operation'],
    methods: {
        show_popup: function (barcode) {
            this.barcodeOpen = barcode;
            this.show_popup_dialog = true;
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
        </td>
      </tr>
      <tr class="teal lighten-2" v-if="operation.barcode">
        <th>Barcode</th>
        <td>{{ operation.barcode }}</td>
      </tr>
      <tr class="teal lighten-2">
        <th>Source</th>
        <td>{{ operation.location_src.name }}
            <v-btn @click="show_popup(operation.location_src.barcode)" icon text class="float-right">
                <v-icon large dark>mdi-help-circle</v-icon>
            </v-btn>
        </td>
      </tr>
      <tr class="amber">
        <th>Destination</th>
        <td>{{ operation.location_dst.name }}
            <v-btn @click="show_popup(operation.location_dst.barcode)" icon text class="float-right">
                <v-icon large dark>mdi-help-circle</v-icon>
            </v-btn>
        </td>
      </tr>
      </tbody>

    <v-dialog v-model="show_popup_dialog">
        <v-card>
            <detail-popup :barcode="barcodeOpen"></detail-popup>
            <v-card-actions>
                <v-btn color="primary" @click="show_popup_dialog = false">Close</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    </template>
  </v-simple-table>
</div>
`,
});
