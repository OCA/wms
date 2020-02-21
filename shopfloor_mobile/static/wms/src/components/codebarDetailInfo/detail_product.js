Vue.component('detail-product', {
    data: function () {
        return {
        };
    },
    props:['productDetail'],
    methods: {
    },
    template: `
        <v-simple-table>
        <template v-slot:default>

          <tbody>
          <tr class="teal lighten-2">
            <td colspan="2">
                {{ productDetail.name }}
            </td>
          </tr>
          <tr class="teal lighten-2">
            <td colspan="2">
                <v-img :src="productDetail.image" max-height="200"></v-img>
            </td>
          </tr>
          <tr class="teal lighten-2">
            <th>Lot</th>
            <td>
                {{ productDetail.lot }}
            </td>
          </tr>
          <tr class="teal lighten-2">
            <th>Expiry date</th>
            <td>
                {{ productDetail.expiry_date }}
            </td>
          </tr>
          <tr class="teal lighten-2">
            <th>Internal ref</th>
            <td>
                {{ productDetail.default_code }}
            </td>
          </tr>
          <tr class="teal lighten-2">
            <th>Supplier ref</th>
            <td>
                {{ productDetail.supplier_code }}
            </td>
          </tr>
          <tr class="teal lighten-2">
            <td colspan="2">
                <div>Packaging</div>
                <ul class="packaging">
                    <li v-for="pack in productDetail.packaging">
                        <span>{{ pack.name }}</span><span>{{ pack.qty }} {{ pack.qty_unit }}</span>
                    </li>
                </ul>
            </td>
          </tr>

          </tbody>

        </template>
      </v-simple-table>
    `,
});
