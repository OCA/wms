
var operationDetail = Vue.component('operation-detail', {
  data: function () {
    return {};
  },
  props:['operation'],
  methods: {},
  template: `
  <div class="detail operation-detail">
    <div class="table-responsive">
      <table class="table">
        <tr class="table-success">
          <th>Name</th>
          <td>{{ operation.name }}</td>
        </tr>
        <tr class="table-success">
          <th>Barcode</th>
          <td>{{ operation.barcode }}</td>
        </tr>
        <tr class="table-success">
          <th class="table-success">Source</th>
          <td>{{ operation.source }}</td>
        </tr>
        <tr class="table-warning">
          <th>Destination</th>
          <td>{{ operation.destination }}</td>
        </tr>
      </table>
    </div>
  </div>
`
})
