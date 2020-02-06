var moreInfo = Vue.component('detail-location', {
    data: function () {
        return {
            "detailInfo": {}
        }
    },
    props:['locationDetail'],
    methods: {
        "created": function (){
            this.detailInfo = this.locationDetail.detail_info;
        }
    },
    template: `
      <div>
        <v-simple-table>
        <template v-slot:default>

          <tbody>
          <tr class="teal lighten-2">
            <th>Location</th>
            <td>
                {{ locationDetail.name }}
            </td>
          </tr>
          <tr class="teal lighten-2">
            <th>Parent</th>
            <td>
                {{ locationDetail.parent_name }}
            </td>
          </tr>
          <tr v-for="product in locationDetail.products" class="blue">

            <td colspan="2">
                {{ product.name }}</br>Pack {{ product.pack }}</br>{{ product.lot }}
                {{ product.qty }}
                <div>In stock 234 / Reserved 92</div>
            </td>

        </tr>
          </tbody>

        </template>
      </v-simple-table>
    </div>
    `
})
