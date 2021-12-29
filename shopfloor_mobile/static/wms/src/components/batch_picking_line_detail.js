/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

// TODO: rename as we used this not only for batch picking
export var batch_picking_line = Vue.component("batch-picking-line-detail", {
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
        defaultDestinationKey: {
            type: String,
            default: "package_dest",
        },
    },
    data() {
        return {
            dialog: false,
        };
    },
    computed: {
        destination() {
            return _.result(this.line, this.$props.defaultDestinationKey);
        },
    },
    template: `
<div v-if="!_.isEmpty(line)" :class="'detail batch-picking-line-detail ' + (line.postponed ? 'line-postponed' : '')">

  <item-detail-card
    :key="'batch-picking-line-detail-1'"
    :record="line"
    :options="{main: true, key_title: 'location_src.name', title_action_field: {action_val_path: 'location_src.barcode'}}"
    :card_color="utils.colors.color_for('screen_step_done')"
    />
  <item-detail-card
    :key="'batch-picking-line-detail-2'"
    :record="line"
    :options="utils.wms.move_line_product_detail_options(line, {fields_blacklist: ['quantity']})"
    :card_color="utils.colors.color_for(articleScanned ? 'screen_step_done': 'screen_step_todo')"
    />

  <item-detail-card
    v-if="articleScanned && destination"
    :key="'batch-picking-line-detail-3'"
    :record="line"
    :options="{main: true, key_title: defaultDestinationKey + '.name', title_action_field:  {action_val_path: defaultDestinationKey + '.name'}}"
    :card_color="utils.colors.color_for(destination ? 'screen_step_done': 'screen_step_todo')"
    />

  <v-card class="pa-2" :color="utils.colors.color_for('screen_step_todo')">
    <packaging-qty-picker
      :key="make_component_key(['packaging-qty-picker', line.id])"
      :options="utils.wms.move_line_qty_picker_options(line)"
      :readonly="!showQtyPicker"
      />
  </v-card>

  <item-detail-card
    v-if="articleScanned && !destination"
    :key="'batch-picking-line-detail-4'"
    :record="line"
    :options="{main: true, title_action_field:  {action_val_path: 'name'}}"
    :card_color="utils.colors.color_for(destination ? 'screen_step_done': 'screen_step_todo')"
    >
    <template v-slot:title>
      Destination not selected.
    </template>
  </item-detail-card>

</div>
`,
});

// TODO: use `misc.line-actions-popup` instead
export var batch_picking_line_actions = Vue.component("batch-picking-line-actions", {
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
  <div class="batch-picking-line-actions">
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
              <btn-action @click="handle_action('action_full_bin')">Go to destination - full bin(s)</btn-action>
            </v-col>
          </v-row>
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <btn-action @click="handle_action('action_skip_line')">Skip line</btn-action>
            </v-col>
          </v-row>
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <btn-action
                  @click="handle_action('action_stock_out')">Declare stock out</btn-action>
            </v-col>
          </v-row>
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <btn-action @click="handle_action('action_change_pack_or_lot')">Change lot or pack</btn-action>
            </v-col>
          </v-row>
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <v-btn x-large @click="dialog = false">Back</v-btn>
            </v-col>
          </v-row>
        </div>
      </v-card>
    </v-dialog>
  </div>
`,
});
