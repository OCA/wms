var moreInfo = Vue.component('detail-pack', {
    data: function () {
        return {
        }
    },
    props:['packDetail'],
    methods: {
    },
    template: `
      <div class="" v-if="">
        <v-simple-table>
        <template v-slot:default>

          <tbody>
          <tr class="teal lighten-2">
            <th>Name</th>
            <td>
                {{ packDetail.name }}
            </td>
          </tr>
          <tr class="blue lighten-2">
            <th>Operation</th>
            <td>Operation Name</td>
          </tr>
          <tr class="blue lighten-2">
            <th>Location</th>
            <td>
                {{ packDetail.location_src.name }}<br/>
                Weight : ?<br/>
                Packaging : ?
            </td>
          </tr>
          <tr v-for="product in packDetail.product" class="blue">
            <th> {{ product.name }}</br> Lot: {{ product.lot }}</th>
            <td>
                {{ product.qty }}
            </td>
        </tr>
          </tbody>

        </template>
      </v-simple-table>
    </div>
    `
})
