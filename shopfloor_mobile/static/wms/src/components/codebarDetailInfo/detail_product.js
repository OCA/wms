Vue.component('detail-product', {
    data: function () {
        return {
        }
    },
    props:['productDetail'],
    methods: {
    },
    template: `

        <v-card outlined>
    <v-card-title>{{ productDetail.name }}</v-card-title>
    <v-card-text>
      <p>Lot ID 029348</p>
      <p class="display-1 text--primary">
        Expiry date
      </p>
      <div class="text--primary">
        And whatever other info.<br>
        Need to show a picture as well.
      </div>
    </v-card-text>
        </v-card>
    `
})
