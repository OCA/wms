/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

export var inventory_line = Vue.component("inventory-line-detail", {
    props: {
        line: Object,
        articleScanned: {
            type: Boolean,
            default: false,
        },
        showQtyPicker: {
            type: Boolean,
            default: false,
        },
    },
    data() {
        return {
            dialog: false,
        };
    },
    template: `
<div v-if="!_.isEmpty(line)" :class="'detail inventory-line-detail ' + (line.postponed ? 'line-postponed' : '')">

  <item-detail-card
    :key="'inventory-line-detail'"
    :record="line"
    :options="utils.wms.inventory_line_product_detail_options(line, {fields_blacklist: ['quantity']})"
    :card_color="utils.colors.color_for(articleScanned ? 'screen_step_done': 'screen_step_todo')"
    />

  <v-card class="pa-2" :color="utils.colors.color_for('screen_step_todo')">
    <packaging-qty-picker
      :key="make_component_key(['packaging-qty-picker', line.id])"
      :options="utils.wms.inventory_line_qty_picker_options(line)"
      :readonly="!showQtyPicker"
      />
  </v-card>

</div>
`,
});

// TODO: use `misc.line-actions-popup` instead
export var inventory_location_actions = Vue.component("inventory-line-actions", {
    props: ["line"],
    data() {
        return {
            dialog: false,
        };
    },
    methods: {
        handle_action(action) {
            this.$emit("action", action);
            this.dialog = false;
        },
    },
    template: `
  <div class="inventory-line-actions">
    <v-dialog v-model="dialog" fullscreen tile class="actions fullscreen text-center">
      <template v-slot:activator="{ on }">
        <div class="button-list button-vertical-list full">
          <v-row class="actions bottom-actions">
            <v-col class="text-center" cols="12">
              <btn-action v-on="on">Action</btn-action>
            </v-col>
          </v-row>
        </div>
      </template>
      <v-card>
        <div class="button-list button-vertical-list full">
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <btn-action @click="handle_action('action_confirm_inventory_line')">Confirm</btn-action>
            </v-col>
          </v-row>
        </div>
      </v-card>
    </v-dialog>
  </div>
`,
});
