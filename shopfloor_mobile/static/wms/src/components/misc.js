/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

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
                <v-btn color="warning" x-large @click="reset">{{ $t('btn.reset.title') }}</v-btn>
            </v-form>
        </div>
    `,
});

Vue.component("cancel-button", {
    template: `
        <div class="action reset">
            <v-btn x-large color="error" v-on:click="$emit('cancel')">{{ $t('btn.cancel.title') }}</v-btn>
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
    props: {
        router_back: {
            type: Boolean,
            default: true,
        },
    },
    methods: {
        on_back: function() {
            this.$root.trigger("go_back");
            if (this.router_back) this.$router.back();
        },
    },
    template: `
<btn-action v-bind="$attrs" action="back" v-on:click="on_back">
  <v-icon>mdi-keyboard-backspace</v-icon><slot>{{ $t("btn.back.title") }}</slot>
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
    template: `<btn-action action="warn" @click="reset_data()">{{ $t('btn.reload_config.title') }}</btn-action>`,
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
              <btn-action v-on="on">{{ $t('misc.actions_popup.btn_action') }}</btn-action>
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
              <v-btn x-large @click="dialog = false"><v-icon>mdi-keyboard-backspace</v-icon> {{ $t('btn.back.title') }}</v-btn>
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

Vue.component("btn-fullscreen", {
    data: function() {
        return {
            fullscreen_on: document.fullscreenElement ? true : false,
        };
    },
    computed: {
        btn_label: function() {
            const transition = this.fullscreen_on ? "exit" : "enter";
            return this.$t("screen.settings.fullscreen." + transition);
        },
    },
    methods: {
        go_fullscreen: function() {
            const elem = document.documentElement;
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.mozRequestFullScreen) {
                /* Firefox */
                elem.mozRequestFullScreen();
            } else if (elem.webkitRequestFullscreen) {
                /* Chrome, Safari & Opera */
                elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) {
                /* IE/Edge */
                elem.msRequestFullscreen();
            }
            this.fullscreen_on = true;
        },
        leave_fullscreen: function() {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            this.fullscreen_on = false;
        },
    },
    template: `
    <btn-action @click="fullscreen_on ? leave_fullscreen() : go_fullscreen()">
        <v-icon>{{ fullscreen_on ? 'mdi-fullscreen-exit' : 'mdi-fullscreen' }}</v-icon> {{ btn_label }}
    </btn-action>
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

Vue.component("speed-dial", {
    props: {
        options: Object,
        fab_btn_attrs: Object,
    },
    data: () => ({
        fab: false,
    }),
    computed: {
        opts() {
            const opts = _.defaults({}, this.$props.options, {
                direction: "top",
                fling: false,
                hover: false,
                tabs: null,
                top: false,
                right: true,
                bottom: true,
                left: false,
                transition: "slide-y-reverse-transition",
                btn_color: "primary",
                fab_btn_icon: "mdi-plus",
            });
            return opts;
        },
    },
    template: `
    <v-speed-dial
        v-bind="$attrs"
        v-model="fab"
        :class="$options._componentTag"
        :top="opts.top"
        :bottom="opts.bottom"
        :right="opts.right"
        :left="opts.left"
        :direction="opts.direction"
        :open-on-hover="opts.hover"
        :transition="opts.transition"
        >
      <template v-slot:activator>
        <v-btn
          v-model="fab"
          :color="opts.btn_color"
          dark
          fab
          v-bind="fab_btn_attrs">
          <v-icon v-if="fab">
            mdi-close
          </v-icon>
          <v-icon v-else v-text="opts.fab_btn_icon"></v-icon>
        </v-btn>
      </template>
      <slot></slot>
    </v-speed-dial>
  `,
});
