
var operationDetail = Vue.component('operation-detail', {
  data: function () {
    return {};
  },
  props:['operation'],
  methods: {},
  template: `
<div>
  <table>
    <tr>
      <th>Source Location</th>
      <td>{{ operation.source }}</td>
    </tr>
    <tr>
      <th>Destination Location</th>
      <td>{{ operation.destination }}</td>
    </tr>
    <tr>
      <th>Id</th>
      <td>{{ operation.id }}</td>
    </tr>
    <tr>
      <th>name</th>
      <td>{{ operation.name }}</td>
    </tr>
  </table>
</div>
  `
})
