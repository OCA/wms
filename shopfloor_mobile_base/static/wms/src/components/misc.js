/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/* eslint-disable strict */

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
            this.$root.loadMenu(true);
            this.$root.$router.push(this.$props.redirect);
        },
    },
    template: `<btn-action action="warn" @click="reset_data()">{{ $t('btn.reload_config.title') }}</btn-action>`,
});

// TODO: make it generic as `actions-btn-popup`
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

Vue.component("profile-not-ready", {
    template: `
    <div :class="$options._componentTag" data-ref="profile-not-ready">
        <v-alert type="warning" tile>
            <p>{{ $t('app.profile_not_configured') }}</p>
        </v-alert>
        <div class="button-list button-vertical-list full">
            <v-row align="center">
                <v-col class="text-center" cols="12">
                    <v-btn @click="$router.push({'name': 'settings'})">
                        <v-icon>mdi-cog</v-icon>
                        <span>{{ $t('app.profile_configure') }}</span>
                    </v-btn>
                </v-col>
            </v-row>
        </div>
    </div>
    `,
});

Vue.component("user-session-detail", {
    props: {
        show_user: {
            type: Boolean,
            default: true,
        },
        show_profile: {
            type: Boolean,
            default: true,
        },
        show_env: {
            type: Boolean,
            default: true,
        },
    },
    template: `
  <div :class="$options._componentTag" data-ref="user-session-detail">
    <v-list>
        <v-list-item v-if="show_env"
                data-ref="session-detail-env"
                :data-id="$root.app_info.running_env"
                >
            <v-list-item-avatar>
                <v-avatar :color="$root.app_info.running_env == 'prod' ? 'primary' : 'warning'" size="36">
                    <v-icon dark>mdi-server</v-icon>
                </v-avatar>
            </v-list-item-avatar>
            <v-list-item-content>
                <span v-text="$t('app.running_env.' + $root.app_info.running_env)" />
            </v-list-item-content>
        </v-list-item>
        <v-list-item v-if="show_user && $root.user.id"
                data-ref="session-detail-user"
                :data-id="$root.user.id"
                >
            <v-list-item-avatar>
                <v-avatar color="primary" size="36">
                    <v-icon dark>mdi-account-circle</v-icon>
                </v-avatar>
            </v-list-item-avatar>
            <v-list-item-content>
                <span v-text="$root.user.name" />
            </v-list-item-content>
        </v-list-item>
        <v-list-item v-if="show_profile && $root.has_profile"
                data-ref="session-detail-profile"
                :data-id="$root.profile.id"
                :to="{name: 'profile'}"
                >
            <v-list-item-avatar>
                <v-avatar color="primary" size="36">
                    <v-icon dark>mdi-account-multiple-check</v-icon>
                </v-avatar>
            </v-list-item-avatar>
            <v-list-item-content>
                <span v-text="$root.profile.name" />
            </v-list-item-content>
        </v-list-item>
    </v-list>
  </div>
  `,
});
