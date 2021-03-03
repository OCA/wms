/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/* eslint-disable strict */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

// TODO: could be merged w/ userConfirmation
Vue.component("last-operation", {
    data: function() {
        return {info: {}};
    },
    template: `
  <div class="last-operation">
      <v-dialog persistent fullscreen tile value=true>
          <v-alert tile type="info" prominent transition="scale-transition">
              <v-card outlined color="blue lighten-1" class="message mt-10">
                  <v-card-title>This was the last operation of the document.</v-card-title>
                  <v-card-text>The next operation is ready to be processed.</v-card-text>
              </v-card>
              <v-form class="mt-10">
                  <v-btn x-large color="success" @click="$emit('confirm')">{{ $t('btn.ok.title') }}</v-btn>
              </v-form>
          </v-alert>
      </v-dialog>
  </div>
  `,
});

Vue.component("get-work", {
    template: `
  <div class="get-work fullscreen-buttons fullscreen-buttons-50">
    <btn-action id="btn-get-work" @click="$emit('get_work')">
      {{ $t('misc.btn_get_work') }}
    </btn-action>
    <btn-action id="btn-manual" color="default" @click="$emit('manual_selection')">
      {{ $t('misc.btn_manual_selection') }}
    </btn-action>
  </div>
  `,
});

Vue.component("stock-zero-check", {
    template: `
  <div class="stock-zero-check">
    <v-dialog fullscreen tile value=true class="actions fullscreen">
      <v-card>
        <div class="button-list button-vertical-list">
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <v-btn x-large color="primary" @click="$emit('action', 'action_confirm_zero')">
                  {{ $t('misc.stock_zero_check.confirm_stock_zero') }}
              </v-btn>
            </v-col>
          </v-row>
          <v-row align="center">
            <v-col class="text-center" cols="12">
              <v-btn x-large color="warning" @click="$emit('action', 'action_confirm_not_zero')">
                  {{ $t('misc.stock_zero_check.confirm_stock_not_zero') }}
              </v-btn>
            </v-col>
          </v-row>
        </div>
      </v-card>
    </v-dialog>
  </div>
`,
});
Vue.component("empty-location-icon", {
    mixins: [ItemDetailMixin],
    template: `
  <v-icon color="orange" :class="$options._componentTag" v-if="record.location_will_be_empty">mdi-alert-rhombus-outline</v-icon>
`,
});

Vue.component("select-zone-item", {
    mixins: [ItemDetailMixin],
    template: `
<div :class="$options._componentTag">
<div class="detail-field mt-2 title">
  <span class="counters">({{ $t("misc.lines_count", record) }})</span>
  <span class="name font-weight-bold">{{ record.name }}</span>
</div>
<div v-for="op_type in record.operation_types" :key="make_component_key([op_type.id])">
  <div class="detail-field mt-2">
    <span class="counters">({{ $t("misc.lines_count", op_type) }})</span>
    <span class="name">{{ op_type.name }}</span>
  </div>
</div>
</div>
  `,
});

Vue.component("cancel-move-line-action", {
    props: {
        record: {
            type: Object,
        },
        options: {
            type: Object,
            default: function() {
                // Take control of which package key (source or destination) is used
                // to cancel the line when cancel line action is available.
                return {
                    package_cancel_key: "package_dest",
                };
            },
        },
    },
    data() {
        return {
            dialog: false,
        };
    },
    methods: {
        on_user_confirm: function(answer) {
            this.dialog = false;
            if (answer === "yes") {
                let data = {};
                if (this.the_package) {
                    data = {package_id: this.the_package.id};
                } else {
                    data = {line_id: this.record.id};
                }
                this.$root.trigger("cancel_picking_line", data);
            }
        },
    },
    computed: {
        // `package` is a reserved identifier!
        the_package: function() {
            return _.result(this.record, this.$props.options.package_cancel_key);
        },
        message: function() {
            const item = this.the_package
                ? this.the_package.name
                : this.record.product.name;
            return "Please confirm cancellation for " + item;
        },
    },
    template: `
<div class="action action-destroy">
<v-dialog v-model="dialog" fullscreen tile class="actions fullscreen text-center">
  <template v-slot:activator="{ on }">
    <v-btn icon class="destroy" x-large rounded color="error" v-on="on"><v-icon>mdi-close-circle</v-icon></v-btn>
  </template>
  <v-card>
    <user-confirmation
        v-on:user-confirmation="on_user_confirm"
        v-bind:question="message"></user-confirmation>
  </v-card>
</v-dialog>
</div>
`,
});

Vue.component("picking-list-item-progress-bar", {
    mixins: [ItemDetailMixin],
    computed: {
        value() {
            return this.utils.wms.picking_completeness(this.record);
        },
    },
    template: `
<div :class="$options._componentTag">
  <v-progress-linear :value="value" color="success" height="8"></v-progress-linear>
</div>
`,
});

Vue.component("line-stock-out", {
    methods: {
        handle_action(action) {
            this.$emit(action);
        },
    },
    template: `
<div :class="$options._componentTag">
  <div class="button-list button-vertical-list full">
    <v-row align="center">
      <v-col class="text-center" cols="12">
        <btn-action @click="handle_action('confirm_stock_issue')">
          {{ $t('misc.stock_zero_check.confirm_stock_zero') }}
        </btn-action>
      </v-col>
    </v-row>
    <v-row align="center">
      <v-col class="text-center" cols="12">
        <btn-back />
      </v-col>
    </v-row>
  </div>
</div>
`,
});
