/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/* eslint-disable strict */
Vue.component("inventory-detail", {
    props: ["record"],
    methods: {
        detail_fields() {
            return [
                {path: "location_count", label: "Total locations"},
                {path: "inventory_line_count", label: "Total lines"},
            ];
        },
    },
    template: `
  <div class="detail inventory-detail with-bottom-actions" v-if="!_.isEmpty(record)">

    <div class="review">

      <item-detail-card :card_color="utils.colors.color_for('screen_step_todo')"
                        :record="record" :options="{main: true, loud: true, fields: detail_fields()}" />

      <div class="button-list button-vertical-list full">
        <v-row align="center">
          <v-col class="text-center" cols="12">
            <btn-action @click="$emit('confirm')">Start</btn-action>
          </v-col>
        </v-row>
        <v-row align="center">
          <v-col class="text-center" cols="12">
            <btn-action :action="'cancel'" @click="$emit('cancel')">Cancel</btn-action>
          </v-col>
        </v-row>
      </div>

    </div>

</div>
`,
});
