
var operationDetail = Vue.component('operation-detail', {
  data: function () {
    return {}
  },
  props:['operation'],
  template: `
  <div class="detail operation-detail" v-if="!_.isEmpty(operation)">
    <v-simple-table>
    <template v-slot:default>
      <tbody>
      <tr class="teal lighten-2" v-if="operation.name">
        <th>Name</th>
        <td>{{ operation.name }}</td>
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
    </template>
  </v-simple-table>
</div>
`
})
