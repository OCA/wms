/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

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
            current_state: {},
            states: {},
            usage: "", // Match component usage on odoo,
            menu_item_id: false,
        };
    },
    watch: {
        "$route.params.menu_id": function() {
            this.menu_item_id = this._get_menu_item_id();
        },
    },
    created: function() {
        this.menu_item_id = this._get_menu_item_id();
    },
    beforeRouteUpdate(to, from, next) {
        // Load initial state
        this._state_load(to.params.state);
        next();
    },
    beforeMount: function() {
        /*
        Ensure initial state is set.
        beforeRouteUpdate` runs only if the route has changed,
        which means that if your reload the page it won't get called :(
        We could use `beforeRouteEnter` but that's not tied to the current instance
        and we won't be able to call `_state_load`.
        */
        this._state_load(this.$route.params.state);
    },
    computed: {
        odoo: function() {
            const odoo_params = this._get_odoo_params();
            return this.$root.getOdoo(odoo_params);
        },
        /*
        Full object of current state.
        TODO: for a future refactoring consider moving out of data `states`
        they are not really data that changes and then we can make them
        standalone object w/ their own class.
        */
        state: {
            get: function() {
                if (_.isEmpty(this.current_state)) {
                    return this._make_current_state();
                }
                return this.current_state;
            },
            set: function(data) {
                this.current_state = this._make_current_state(data);
            },
        },
        search_input_placeholder: function() {
            const placeholder = this.state.display_info.scan_placeholder;
            return _.isFunction(placeholder) ? placeholder.call(this) : placeholder;
        },
        show_cancel_button: function() {
            return this.state.display_info.show_cancel_button;
        },
        screen_info: function() {
            return {
                // you can provide a different screen title
                title: this.screen_title ? this.screen_title() : this.menu_item().name,
                current_doc: this.current_doc ? this.current_doc() : null,
                klass: this.screen_klass(),
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
        /**
         * Retrieve Odoo connection params.
         */
        _get_odoo_params: function() {
            return {
                process_menu_id: this.menu_item_id,
                profile_id: this.$root.profile.id,
                usage: this.usage,
            };
        },
        /**
         * Retrieve current menu item ID.
         */
        _get_menu_item_id: function() {
            const menu_id = Number.parseInt(this.$route.params.menu_id, 10);
            if (Number.isNaN(menu_id)) {
                /*
                It's very handy for demo data to reference always the same menu id.
                Since the menu id is included in the URL
                it allows to reload the page w/out having to refresh menu items.
                This way you can define multiple scenario w/ different menu items
                and you can tag them with the same reusable label (eg: case_1).
                */
                return this.$route.params.menu_id;
            }
            return menu_id;
        },
        /**
         * Retrieve state specification.
         *
         * States are described through `this.states` object.
         * This function returns their specification object.
         * Defaults to current state.
         *
         * @param {*} state_key: a state key other that current_state_key
         */
        _get_state_spec: function(state_key) {
            // TODO: this function is the 1st step towards moving state definition
            // out of the component data (which makes no sense).
            return this.states[state_key || this.current_state_key];
        },
        /**
         * Build a wrapped state object based on current state.
         *
         * The returned object is a bundle of current state data
         * and current state specification.
         *
         * @param {*} data
         */
        _make_current_state: function(data = {}) {
            const state = {
                key: this.current_state_key,
                data: data,
            };
            _.extend(state, this._get_state_spec());
            _.defaults(state, {display_info: {}});
            return state;
        },
        screen_klass: function() {
            return this.usage + " " + "state-" + this.current_state_key;
        },
        menu_item: function() {
            const self = this;
            return _.head(
                _.filter(this.$root.appmenu.menus, function(m) {
                    return m.id === self.menu_item_id;
                })
            );
        },
        make_state_component_key: function(bits) {
            bits.unshift(this.current_state_key);
            bits.unshift(this.usage);
            return this.make_component_key(bits);
        },
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
                        menu_id: this.menu_item_id,
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
            state_key = state_key || this.current_state_key;
            this.$root.$storage.remove(this.storage_key(state_key));
        },
        _state_get_data: function(state_key) {
            return this.$root.$storage.get(this.storage_key(state_key), {});
        },
        _state_set_data: function(state_key, v) {
            this.$root.$storage.set(this.storage_key(state_key), v);
        },
        state_get_data: function(state_key) {
            state_key = state_key || this.current_state_key;
            return this._state_get_data(state_key);
        },
        state_set_data: function(data, state_key, reload_state = true) {
            state_key = state_key || this.current_state_key;
            const new_data = _.merge({}, this.state_get_data(state_key), data);
            // Trigger update of computed `state.data` and refreshes the UI.
            this._state_set_data(state_key, new_data);
            if (reload_state) {
                this._reload_current_state();
            }
        },
        _reload_current_state: function() {
            // Force re-computation of current state data.
            this.state = this.state_get_data();
            this.$root.trigger("screen:reload", {}, true);
        },
        state_reset_data_all() {
            const self = this;
            const keys_to_clear = _.filter(this.$storage.keys(), x => {
                return x.includes(self.usage);
            });
            keys_to_clear.forEach(key => {
                // Key includes the whole string w/ prefix, need the state key only
                self.state_reset_data(_.last(key.split(".")));
            });
        },
        /*
            Loads a new state, handle transition, setup event handlers.
        */
        _state_load: function(state_key, promise) {
            if (state_key == "init") {
                /*
                Alias "init" to the initial state
                and erase all existing data if any.
                Used when we enter from a menu or to enforce data cleanup
                or any other case where you want to erase all data on demand.
                */
                this.state_reset_data_all();
                this.reset_notification();
                /**
                 * Special case: if `init` is defined as state
                 * you can use it do particular initialization.
                 * Eg: call the server to preload some data.
                 * In this case the state is responsible
                 * for handline the transition to another state
                 * or delegate it to server result via `next_state` key.
                 */
                if (!("init" in this.states)) {
                    state_key = this.initial_state_key;
                }
            }
            state_key = state_key || "start";
            if (state_key == "start") {
                // Alias "start" to the initial state
                state_key = this.initial_state_key;
            }
            if (!_.has(this.states, state_key)) {
                alert("State `" + state_key + "` does not exists!");
            }
            if (this.current_state_key) {
                // Exiting another state
                this.on_state_exit();
            }
            this.current_state_key = state_key;
            this._reload_current_state();
            if (promise) {
                promise.then();
            } else {
                this.on_state_enter();
            }
            this._state_bind_events();
            // notify root
            this.$root.$emit("state:change", this._global_state_key(state_key));
        },
        _global_state_key: function(state_key) {
            return this.usage + "/" + state_key;
        },
        wait_call: function(promise, callback) {
            return promise.then(this.on_call_success, this.on_call_error);
        },
        on_state_enter: function() {
            const state = this._get_state_spec();
            if (state.enter) {
                state.enter();
            }
        },
        on_state_exit: function() {
            const state = this._get_state_spec();
            if (state.exit) {
                state.exit();
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
            let state_key = result.next_state;
            // TODO: potentially we can return values for other states as well.
            // We should loop on result.data keys.
            const state_data = result.data[state_key];
            if (state_key == "start") {
                state_key = this.initial_state_key;
            }
            if (!_.isUndefined(state_data)) {
                this.state_reset_data(state_key);
                // Set state data but delay state wrapper reload.
                this.state_set_data(state_data, state_key, false);
            }
            this.reset_notification();
            if (result.message) {
                this.set_message(result.message);
            }
            if (result.popup) {
                this.set_popup(result.popup);
            }
            if (state_key == this.$route.params.state) {
                // As we stay on the same state, just refresh state wrapper data
                this._reload_current_state();
            } else {
                // Move to new state, data will be refreshed right after.
                this.state_to(state_key);
            }
        },
        on_call_error: function(result) {
            alert(result.status + " " + result.error);
        },
        on_reset: function(e) {
            this.state_reset_data_all();
            this.reset_notification();
            this.state_to("start");
        },
        // Specific states methods
        on_scan: function(scanned) {
            // Prevent scanning twice
            if (this.$root.loading) return;
            const state = this._get_state_spec();
            if (state.on_scan) {
                state.on_scan(scanned);
            }
        },
        // TODO: get rid of this as it's used on cluster_picking only and
        // we can use state events binding.
        on_cancel: function() {
            const state = this._get_state_spec();
            if (state.on_cancel) {
                state.on_cancel();
            }
        },
        on_user_confirm: function(answer) {
            const state = this._get_state_spec();
            state.on_user_confirm(answer);
            this.need_confirmation = false;
            this.reset_notification();
        },
        set_message: function(message) {
            this.$set(this.messages, "message", message);
        },
        set_popup: function(popup) {
            this.$set(this.messages, "popup", popup);
        },
        reset_notification: function() {
            this.$set(this.messages, "message", {body: null, message_type: null});
            this.$set(this.messages, "popup", {body: null});
        },
        display_app_error: function(error) {
            let parts = [error.status, error.name];
            if (error.description) {
                parts.push("\n" + error.description);
            }
            this.set_message({
                body: parts.join(" "),
                message_type: "error",
                support_url: error.log_entry_url,
                support_url_text: this.$t("app.log_entry_link"),
            });
        },
        _state_bind_events: function() {
            const state = this._get_state_spec();
            if (state.events) {
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
                _.each(state.events, function(handler, name) {
                    if (typeof handler == "string") handler = state[handler];
                    const event_name =
                        self._global_state_key(self.state.key) + ":" + name;
                    const existing = self.$root.event_hub._events[event_name];
                    if (!_.isEmpty(existing)) {
                        self.$root.event_hub.$off(event_name);
                    }
                    if (handler) {
                        self.$root.event_hub.$on(event_name, handler);
                    }
                });
            }
        },
    },
};
