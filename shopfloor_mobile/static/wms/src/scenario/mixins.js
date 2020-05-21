export var ScenarioBaseMixin = {
    data: function() {
        return {
            messages: {
                message: {
                    body: "",
                    message_type: "",
                },
                popup: {
                    body: "",
                },
            },
            need_confirmation: false,
            show_reset_button: false,
            initial_state_key: "start",
            current_state_key: "",
            states: {},
            usage: "", // Match component usage on odoo,
        };
    },
    beforeRouteUpdate(to, from, next) {
        // Load initial state
        this._state_load(to.params.state);
        next();
    },
    beforeMount: function() {
        if (this.$root.demo_mode) {
            this.$root.loadJS("src/demo/demo." + this.usage + ".js", this.usage);
            // this should be always loaded
            this.$root.loadJS("src/demo/demo.scan_anything.js", "scan_anything");
        }
        /*
        Ensure initial state is set.
        beforeRouteUpdate` runs only if the route has changed,
        which means that if your reload the page it won't get called :(
        We could use `beforeRouteEnter` but that's not tied to the current instance
        and we won't be able to call `_state_load`.
        */
        this._state_load(this.$route.params.state);
    },
    mounted: function() {
        const odoo_params = {
            process_menu_id: this.menu_item.id,
            profile_id: this.$root.profile.id,
            usage: this.usage,
        };
        this.odoo = this.$root.getOdoo(odoo_params);
    },
    computed: {
        menu_item: function() {
            const self = this;
            return _.head(
                _.filter(this.$root.appmenu.menus, function(m) {
                    return m.id === parseInt(self.$route.params.menu_id, 10);
                })
            );
        },
        /*
        Full object of current state.
        TODO: for a future refactoring consider moving out of data `states`
        they are not really data that changes and then we can make them
        standalone object w/ their own class.
        */
        state: function() {
            const state = {
                key: this.current_state_key,
                data: this.state_get_data(),
            };
            _.extend(state, this.states[this.current_state_key]);
            _.defaults(state, {display_info: {}});
            return state;
        },
        search_input_placeholder: function() {
            if (this.state.scan_placeholder) {
                // TMP backward compat
                return this.state.scan_placeholder;
            }
            return this.state.display_info.scan_placeholder;
        },
        show_cancel_button: function() {
            return this.state.display_info.show_cancel_button;
        },
        screen_info: function() {
            return {
                // you can provide a different screen title
                title: this.screen_title || this.menu_item.name,
                klass: this.usage + " " + "state-" + this.state.key,
                user_message: this.user_message,
                user_popup: this.user_popup,
                noUserMessage: this.need_confirmation,
            };
        },
        user_message: function() {
            if (_.result(this.messages, "message.body")) {
                return this.messages.message;
            }
            return null;
        },
        user_popup: function() {
            if (_.result(this.messages, "popup.body")) {
                return this.messages.popup;
            }
            return null;
        },
    },
    methods: {
        storage_key: function(state_key) {
            state_key = _.isUndefined(state_key) ? this.current_state_key : state_key;
            return this.usage + "." + state_key;
        },
        /*
        Switch state to given one.
        */
        state_to: function(state_key) {
            const self = this;
            return this.$router
                .push({
                    name: this.usage,
                    params: {
                        menu_id: this.menu_item.id,
                        state: state_key,
                    },
                })
                .catch(() => {
                    // see https://github.com/quasarframework/quasar/issues/5672
                    console.error("No new route found");
                });
        },
        // Generic states methods
        state_is: function(state_key) {
            return state_key == this.current_state_key;
        },
        state_in: function(state_keys) {
            return _.filter(state_keys, this.state_is).length > 0;
        },
        state_reset_data: function(state_key) {
            this.$root.$storage.remove(this.storage_key(state_key));
        },
        _state_get_data: function(storage_key) {
            return this.$root.$storage.get(storage_key, {});
        },
        _state_set_data: function(storage_key, v) {
            this.$root.$storage.set(storage_key, v);
        },
        state_get_data: function(state_key) {
            return this._state_get_data(this.storage_key(state_key));
        },
        state_set_data: function(data, state_key) {
            const new_data = _.merge({}, this.state_get_data(state_key), data);
            // Trigger update of computed `state.data` and refreshes the UI.
            this._state_set_data(this.storage_key(state_key), new_data);
            this.$set(
                this.states[state_key || this.current_state_key],
                "data",
                new_data
            );
        },
        /*
            Load given state, handle transition, setup event handlers.
        */
        _state_load: function(state_key, promise) {
            state_key = state_key || "start";
            if (state_key == "start") {
                // Alias "start" to the initial state
                state_key = this.initial_state_key;
            }
            if (!_.has(this.states, state_key)) {
                alert("State `" + state_key + "` does not exists!");
            }
            this.on_state_exit();
            this.current_state_key = state_key;
            if (promise) {
                promise.then();
            } else {
                this.on_state_enter();
            }
            this._state_bind_events();
            // notify root
            // TODO: maybe not needed after introducing routing
            this.$root.$emit("state:change", state_key);
        },
        // TODO: refactor all transitions to state `wait_call` with this call
        wait_call: function(promise) {
            return promise.then(this.on_call_success, this.on_call_error);
        },
        on_state_enter: function() {
            if (this.state.enter) {
                this.state.enter();
            }
        },
        on_state_exit: function() {
            if (this.state.exit) {
                this.state.exit();
            }
        },
        on_call_success: function(result) {
            if (_.isUndefined(result)) {
                console.error(result);
                alert("Something went wrong. Check log.");
            }
            if (result.error) {
                this.display_app_error(result.error);
                return;
            }
            const state_key =
                result.next_state == "start"
                    ? this.initial_state_key
                    : result.next_state;
            if (!_.isUndefined(result.data)) {
                // TODO: we should find a way to reset the whole scenario data
                // as soon as we start w/ the scenario by clicking the menu item
                // and not just when you go to /start because you could get back
                // to it from another state.
                this.state_reset_data(state_key);
                this.state_set_data(result.data[state_key], state_key);
            }
            this.reset_notification();
            if (result.message) {
                this.set_message(result.message);
            }
            if (result.popup) {
                this.set_popup(result.popup);
            }
            if (this.current_state_key != state_key) {
                this.state_to(state_key);
            }
        },
        on_call_error: function(result) {
            alert(result.status + " " + result.error);
        },
        on_reset: function(e) {
            this.state_reset_data();
            this.reset_notification();
            this.state_to("start");
        },
        // Specific states methods
        on_scan: function(scanned) {
            if (this.state.on_scan) {
                this.state.on_scan(scanned);
            }
        },
        // TODO: check if we really need these
        // as we have state event handlers auto binding.
        // on_select: function(selected) {
        //     if (this.state.on_select) {
        //         this.state.on_select(selected);
        //     }
        // },
        // on_back: function() {
        //     if (this.state.on_back) {
        //         this.state.on_back();
        //     }
        // },
        // TODO: get rid of this as it's used on cluster_picking only and
        // we can use state events binding.
        on_cancel: function() {
            if (this.state.on_cancel) {
                this.state.on_cancel();
            }
        },
        on_user_confirm: function(answer) {
            this.state.on_user_confirm(answer);
            this.need_confirmation = false;
            this.reset_notification();
        },
        set_message: function(message) {
            this.messages.message = message;
        },
        set_popup: function(popup) {
            this.messages.popup.body = popup.body;
        },
        reset_notification: function() {
            this.messages.message = null;
            this.messages.message_type = null;
            this.messages.popup.body = null;
        },
        display_app_error: function(error) {
            this.set_message({
                body: error.description,
                message_type: "error",
            });
        },
        _state_bind_events: function() {
            if (this.state.events) {
                /*
                Automatically bind events defined by states.
                A state can define `events` w/ this structure:

                    events: {
                        '$event_name': '$handler',
                    },

                `$handler_name` must match a function or the name of a function
                available in the state.

                The event name is prefixed w/ the state key so that
                any component can subscribe globally,
                via the event hub at root level,
                to a particular event fired on a specific state
                */
                const self = this;
                _.each(self.state.events, function(handler, name) {
                    if (typeof handler == "string") handler = self.state[handler];
                    const event_name = self.state.key + ":" + name;
                    // Wipe old handlers
                    // TODO: any way to register them just once?
                    self.$root.event_hub.$off(event_name, handler);
                    self.$root.event_hub.$on(event_name, handler);
                });
            }
        },
    },
};

// TODO: move it back it the transfer scenario when we get rid of
// the putaway scenario
export var SinglePackStatesMixin = {
    data: function() {
        return {
            states: {
                // Generic state for when to start w/ scanning a pack
                start_scan_pack: {
                    display_info: {
                        title: "Start by scanning a pack",
                        scan_placeholder: "Scan pack",
                    },
                    enter: () => {
                        this.state_reset_data();
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("start", {barcode: scanned.text})
                        );
                    },
                },
                // Generic state for when to start w/ scanning a pack or loc
                start_scan_pack_or_location: {
                    display_info: {
                        title: "Start by scanning a pack or a location",
                        scan_placeholder: "Scan pack",
                    },
                    enter: () => {
                        this.state_reset_data();
                    },
                    on_scan: scanned => {
                        this.wait_call(
                            this.odoo.call("start", {barcode: scanned.text})
                        );
                    },
                },
                // TODO: these states should be splitted out to a specific mixin
                // for putaway and pack transfer
                scan_location: {
                    display_info: {
                        title: "Set a location",
                        scan_placeholder: "Scan location",
                        show_cancel_button: true,
                    },
                    on_scan: (scanned, confirmation = false) => {
                        this.state_set_data({location_barcode: scanned.text});
                        this.wait_call(
                            this.odoo.call("validate", {
                                package_level_id: this.state.data.id,
                                location_barcode: scanned.text,
                                confirmation: confirmation,
                            })
                        );
                    },
                    on_cancel: () => {
                        this.wait_call(
                            this.odoo.call("cancel", {
                                package_level_id: this.state.data.id,
                            })
                        );
                    },
                },
                confirm_location: {
                    display_info: {
                        scan_placeholder: "Scan location",
                    },
                    enter: () => {
                        this.need_confirmation = true;
                    },
                    exit: () => {
                        this.need_confirmation = false;
                    },
                    on_user_confirm: answer => {
                        if (answer == "yes") {
                            // Reuse data from scan_location and
                            // simulate the event that on_scan expects
                            const scan_data = this.state_get_data("scan_location");
                            this.state.on_scan(
                                {
                                    text: scan_data.location_barcode,
                                },
                                true
                            );
                        } else {
                            this.state_to("scan_location");
                        }
                    },
                    on_scan: (scanned, confirmation = true) => {
                        this.on_state_exit();
                        // FIXME: use state_load
                        this.current_state_key = "scan_location";
                        this.state.on_scan(scanned, confirmation);
                    },
                },
                confirm_start: {
                    display_info: {
                        title: "Confirm start and select a location",
                        scan_placeholder: "Scan location",
                    },
                    enter: () => {
                        this.need_confirmation = true;
                    },
                    exit: () => {
                        this.need_confirmation = false;
                    },
                    on_user_confirm: answer => {
                        if (answer == "yes") {
                            // Keep the data received from previous state but not the question answered
                            const state_data = this.state_get_data(
                                this.current_state_key
                            );
                            state_data.message = {};
                            this.state_set_data(state_data, "scan_location");
                            this.state_to("scan_location");
                        } else {
                            this.state_to("start");
                        }
                    },
                    on_scan: scanned => {
                        this.on_state_exit();
                        this.current_state_key = "scan_location";
                        this.state.on_scan(scanned);
                    },
                },
            },
        };
    },
};
