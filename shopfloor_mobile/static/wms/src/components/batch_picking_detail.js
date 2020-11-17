/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/* eslint-disable strict */
Vue.component("batch-picking-detail", {
    props: ["record"],
    methods: {
        detail_fields() {
            return [
                {path: "picking_count", label: "Total operations"},
                {path: "move_line_count", label: "Total lines"},
                {path: "weight", label: "Total weight"},
            ];
        },
        picking_detail_fields() {
            return [
                {path: "name", klass: "loud", action_val_path: "name"},
                {path: "move_line_count", label: "Lines"},
                {path: "weight", label: "Weight"},
            ];
        },
        picking_list_options() {
            return {
                group_title_default: "Pickings list",
                group_color: this.utils.colors.color_for("screen_step_todo"),
                list_item_options: {
                    key_title: "name",
                    loud_title: true,
                    fields: this.picking_detail_fields(),
                },
            };
        },
    },
    template: `
  <div class="detail batch-picking-detail with-bottom-actions" v-if="!_.isEmpty(record)">

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

    <div class="pickings">
      <list
          :records="record.pickings"
          :options="picking_list_options()"
          />
    </div>

</div>
`,
});
