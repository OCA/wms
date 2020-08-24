/* eslint-disable strict */
import {ItemDetailMixin} from "./detail/detail_mixin.js";

Vue.component("reset-screen-button", {
    props: ["show_reset_button"],
    methods: {
        reset: function() {
            this.$emit("reset");
        },
    },
    template: `
        <div class="action reset" v-if="show_reset_button">
            <v-form class="m-t5"  v-on:reset="reset">
                <v-btn color="warning" x-large @click="reset">Reset</v-btn>
            </v-form>
        </div>
    `,
});

Vue.component("cancel-button", {
    template: `
        <div class="action reset">
            <v-btn x-large color="error" v-on:click="$emit('cancel')">Cancel</v-btn>
        </div>
    `,
});

// TODO: could be merged w/ userConfirmation
Vue.component("last-operation", {
    // Props: ['info'],
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
                    <v-btn x-large color="success" @click="$emit('confirm')">OK</v-btn>
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
          Get work
      </btn-action>
      <btn-action id="btn-manual" color="default" @click="$emit('manual_selection')">
          Manual selection
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
                <v-btn x-large color="primary" @click="$emit('action', 'action_confirm_zero')">Confirm stock = 0</v-btn>
              </v-col>
            </v-row>
            <v-row align="center">
              <v-col class="text-center" cols="12">
                <v-btn x-large color="warning" @click="$emit('action', 'action_confirm_not_zero')">Confirm stock NOT empty</v-btn>
              </v-col>
            </v-row>
          </div>
        </v-card>
      </v-dialog>
    </div>
  `,
});

Vue.component("state-display-info", {
    props: {
        info: Object,
    },
    computed: {
        title: function() {
            return _.isFunction(this.info.title) ? this.info.title() : this.info.title;
        },
    },
    template: `
  <div class="state-display-info" v-if="title">
    <v-alert tile dense type="info" :icon="false">
      <div class="state-title">{{ title }}</div>
    </v-alert>
  </div>
`,
});

Vue.component("edit-action", {
    props: {
        record: Object,
        options: {
            type: Object,
            default: function() {
                return {
                    click_event: "edit",
                };
            },
        },
    },
    template: `
<div class="action action-edit">
  <v-btn icon class="edit" x-large rounded color="default"
         @click="$root.trigger(options.click_event, record)"><v-icon>mdi-pencil-outline</v-icon></v-btn>
</div>
`,
});

Vue.component("separator-title", {
    template: `
  <h3 class="separator-title"><slot></slot></h3>
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
            return this.utils.misc.picking_completeness(this.record);
        },
    },
    template: `
  <div :class="$options._componentTag">
    <v-progress-linear :value="value" color="success" height="8"></v-progress-linear>
  </div>
`,
});

// handy component to place UI todos
Vue.component("todo", {
    template: `
<div :class="$options._componentTag">
  <div class="message">
    <v-icon>mdi-hammer-wrench</v-icon> <strong>TODO: <small><slot></slot></small></strong>
  </div>
</div>
`,
});

// TODO: use color registry for the icon color
Vue.component("btn-info-icon", {
    props: {
        color: {
            type: String,
        },
    },
    template: `
    <v-icon :color="color || utils.colors.color_for('info_icon')">mdi-information</v-icon>
`,
});

// TODO: move to separated file
Vue.component("btn-action", {
    props: {
        action: {
            type: String,
            default: "",
        },
        color: {
            type: String,
            default: "",
        },
    },
    computed: {
        btn_color() {
            let color = this.color;
            if (!color) {
                color = this.utils.colors.color_for(
                    this.action ? "btn_action_" + this.action : "btn_action"
                );
            }
            return color;
        },
    },
    template: `
  <v-btn x-large v-bind="$attrs" v-on="$listeners" :color="btn_color">
    <slot></slot>
  </v-btn>
`,
});

Vue.component("btn-back", {
    methods: {
        on_back: function() {
            this.$root.trigger("go_back");
            this.$router.back();
        },
    },
    template: `
<btn-action v-bind="$attrs" action="back" v-on:click="on_back">
  <v-icon>mdi-keyboard-backspace</v-icon>{{ $t("btn.back.title") }}
</btn-action>
`,
});

Vue.component("btn-reset-config", {
    props: {
        redirect: {
            type: Object,
            default: function() {
                return {name: "home"};
            },
        },
    },
    methods: {
        reset_data: function() {
            this.$root._clearConfig();
            this.$root._loadMenu();
            this.$root.$router.push(this.$props.redirect);
        },
    },
    template: `<btn-action action="warn" @click="reset_data()">Reload config and menu</btn-action>`,
});

Vue.component("line-actions-popup", {
    props: {
        line: {
            type: Object,
        },
        actions: {
            type: Array,
            default: function() {
                return [];
            },
        },
    },
    data() {
        return {
            dialog: false,
        };
    },
    methods: {
        handle_action(action) {
            this.dialog = false;
            this.$emit("action", action);
        },
    },
    template: `
  <div :class="$options._componentTag">
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
          <v-row align="center" v-for="action in actions">
            <v-col class="text-center" cols="12">
              <btn-action @click="handle_action(action)">{{ action.name }}</btn-action>
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
          <btn-action @click="handle_action('confirm_stock_issue')">Confirm stock = 0</btn-action>
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

Vue.component("screen-loading", {
    props: {
        loading: {
            type: Boolean,
        },
    },
    template: `
    <v-overlay :value="loading" opacity="0.6">
      <v-row
          align="center"
          justify="center">
          <v-col cols="12" class="text-center">
              <v-progress-circular indeterminate :color="utils.colors.color_for('spinner')" />
              <p class="mt-4">Waiting...</p>
          </v-col>
      </v-row>
    </v-overlay>
  `,
});
