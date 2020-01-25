
var operationDetail = Vue.component('operation-detail', {
  data: function () {
    return {}
  },
  props:['operation'],
  template: `
  <div class="detail operation-detail" v-if="!_.isEmpty(operation)">
    <div class="table-responsive">
      <table class="table">
        <tr class="table-success" v-if="operation.name">
          <th>Name</th>
          <td>{{ operation.name }}</td>
        </tr>
        <tr class="table-success" v-if="operation.barcode">
          <th>Barcode</th>
          <td>{{ operation.barcode }}</td>
        </tr>
        <tr class="table-success">
          <th class="table-success">Source</th>
          <td>{{ operation.location_src.name }}</td>
        </tr>
        <tr class="table-warning">
          <th>Destination</th>
          <td>{{ operation.location_dst.name }}</td>
        </tr>
      </table>
    </div>
  </div>
`
})
