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
                <v-btn depressed color="warning" x-large @click="reset">Reset</v-btn>
            </v-form>
        </div>
    `,
});

Vue.component("cancel-button", {
    template: `
        <div class="action reset">
            <v-btn depressed x-large color="error" v-on:click="$emit('cancel')">Cancel</v-btn>
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
      <v-btn id="btn-get-work" color="success" @click="$emit('get_work')">
          Get work
      </v-btn>
      <v-btn id="btn-manual" color="default" @click="$emit('manual_selection')">
          Manual selection
      </v-btn>
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
                <v-btn depressed x-large color="primary" @click="$emit('action', 'action_confirm_zero')">Confirm stock = 0</v-btn>
              </v-col>
            </v-row>
            <v-row align="center">
              <v-col class="text-center" cols="12">
                <v-btn depressed x-large color="warning" @click="$emit('action', 'action_confirm_not_zero')">Confirm stock NOT empty</v-btn>
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
    template: `
  <div class="state-display-info" v-if="info.title">
    <div class="container">
      <v-alert tile dense outlined type="info">
        <div class="state-title text--secondary">{{ info.title }}</div>
      </v-alert>
    </div>
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
  <v-btn icon class="edit" depressed x-large rounded color="default"
         @click="$root.trigger(options.click_event, record)"><v-icon>mdi-pencil-outline</v-icon></v-btn>
</div>
`,
});

Vue.component("btn-back", {
    template: `
  <v-btn depressed x-large color="default" v-on:click="$router.back()">{{ $t("btn.back.title") }}</v-btn>
  `,
});

Vue.component("separator-title", {
    template: `
  <h3 class="separator-title"><slot></slot></h3>
`,
});

Vue.component("cancel-move-line-action", {
    props: ["record"],
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
                if (this.record.package_dest) {
                    data = {package_id: this.record.package_dest.id};
                } else {
                    data = {line_id: this.record.id};
                }
                this.$root.trigger("cancel_picking_line", data);
            }
        },
    },
    computed: {
        message: function() {
            const item = this.record.package_dest
                ? this.record.package_dest.name
                : this.record.product.name;
            return "Please confirm cancellation for " + item;
        },
    },
    template: `
<div class="action action-destroy">
  <v-dialog v-model="dialog" fullscreen tile class="actions fullscreen text-center">
    <template v-slot:activator="{ on }">
      <v-btn icon class="destroy" depressed x-large rounded color="error" v-on="on"><v-icon>mdi-close-circle</v-icon></v-btn>
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
