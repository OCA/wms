var moreInfo = Vue.component('detail-operation', {
    props:['operationDetail'],
    template: `
      <div>
        <v-simple-table>
        <template v-slot:default>

          <tbody>
          <tr class="teal lighten-2">
            <th>Operation</th>
            <td>
                {{ operationDetail.name }}
            </td>
          </tr>
          <tr class="teal lighten-2">
            <td colspan="2">
                Lots of information about the operation.
            </td>
          </tr>
          <tr v-for="move in operationDetail.moves" class="blue">

            <td colspan="2">
                {{ move.name }}</br>
                Quantity {{ move.qty }}</br>
                {{ move.lot }}
            </td>

        </tr>
          </tbody>

        </template>
      </v-simple-table>
    </div>
    `
})
