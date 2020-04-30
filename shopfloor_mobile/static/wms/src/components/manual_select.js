/* eslint-disable strict */
Vue.component("manual-select", {
    props: {
        records: {
            type: Array,
            default: function() {
                return [];
            },
        },
        grouped_records: {
            type: Array,
            default: function() {
                return [];
            },
        },
        key_title: {
            type: String,
            default: "name",
        },
        options: {
            type: Object,
        },
        list_item_fields: {
            type: Array,
            default: function() {
                return [];
            },
        },
        selected_event: {
            type: String,
            default: "select",
        },
    },
    data: function() {
        return {
            selected: null,
        };
    },
    mounted() {
        // Relies on properties
        this.selected = this._initSelected();
    },
    methods: {
        _initSelected() {
            const initValue = this.opts.initValue;
            let selected = false;
            if (this.opts.multiple) {
                selected = initValue ? initValue : [];
                if (this.opts.initSelectAll) {
                    selected = [];
                    _.each(this.records, function(rec, __) {
                        selected.push(rec.id);
                    });
                }
            } else {
                selected = initValue ? initValue : false;
            }
            return selected;
        },
        _getSelected() {
            const self = this;
            let selected_records = null;
            if (this.opts.multiple) {
                selected_records = _.filter(self.records, function(o) {
                    return self.selected.includes(o.id);
                });
            } else {
                selected_records = _.head(
                    _.filter(self.records, function(o) {
                        return self.selected === o.id;
                    })
                );
            }
            return selected_records;
        },
        /*
        You may wonder why I'm not using `v-model` on checkboxes
        as well as why we don't use `list-item-group` from vuetify
        that makes list selectable.

        1st of all: I tried them both.
        I had to give up after quite some battling. :(

        Concatenation of reasons:

        * they work smoothly until you do simple things
        * if you want to bind @click event
          (eg: to do more things based on the target) it breaks selection
        * if you bind @change event you have no full event, only the value
        * if you use `watch` it gets triggered on 1st load, which we don't want
          and it's very tricky to if not impossible to manage additional events.

        Hence, the sad decision: write my own value/event handlers.
        */
        _updateValue(value, add) {
            if (this.opts.multiple) {
                if (add) {
                    this.selected.push(value);
                } else {
                    _.pull(this.selected, value);
                }
            } else {
                // eslint-disable-next-line no-lonely-if
                if (add) {
                    this.selected = value;
                } else {
                    this.selected = false;
                }
            }
        },
        handleSelect(rec, event) {
            const elem = event.target;
            this._updateValue(parseInt(elem.value, 10), elem.checked);
            $(elem)
                .closest(".list-item-wrapper")
                .toggleClass("active", elem.checked);
            if (!this.opts.showActions) {
                this._emitSelected(this._getSelected());
            }
        },
        _emitSelected(data) {
            this.$root.trigger(this.opts.selected_event, data);
            // You can subscribe to local event too
            this.$emit(this.opts.selected_event, data);
        },
        handleAction(action) {
            this._emitSelected(this._getSelected());
        },
        is_selected(rec) {
            if (!this.valued) {
                return false;
            }
            return this.opts.multiple
                ? this.selected.includes(rec.id)
                : this.selected === rec.id;
        },
    },
    computed: {
        has_records() {
            return this.records.length > 0;
        },
        opts() {
            // Defining defaults for an Object property
            // works only if you don't pass the property at all.
            // If you pass only one key, you'll lose all defaults.
            const opts = _.defaults({}, this.$props.options, {
                showActions: true,
                initSelectAll: false,
                initValue: null,
                multiple: false,
                showCounters: false,
                list_item_component: "list-item",
                list_item_extra_component: "",
                selected_event: "select",
            });
            return opts;
        },
        list_item_options() {
            return {
                key_title: this.key_title,
                showCounters: this.opts.showCounters,
                fields: this.opts.list_item_fields,
            };
        },
        selectable() {
            if (!this.grouped_records.length) {
                // Simulate grouping (allows to keep template the same)
                return [{key: "no-group", title: "", records: this.records}];
            }
            return this.grouped_records;
        },
        klass() {
            const bits = ["manual-select"];
            _.forEach(this.opts, function(v, k) {
                if (v) {
                    let bit = "with-" + k;
                    if (typeof v === "string") {
                        bit += "--" + v;
                    }
                    bits.push(bit);
                }
            });
            return bits.join(" ");
        },
        valued() {
            if (this.selected === null) {
                return false;
            }
            return this.opts.multiple
                ? this.selected.length > 0
                : this.selected !== false;
        },
    },
    template: `
    <div :class="klass">
        <v-card outlined>
            <v-list v-if="has_records">
                <div class="select-group" v-for="(group, gindex) in selectable" :key="'group-' + gindex">
                    <v-card-title v-if="group.title">{{ group.title }}</v-card-title>
                    <div :class="'list-item-wrapper' + (is_selected(rec) ? ' active' : '')" v-for="(rec, index) in group.records"">
                        <v-list-item :key="gindex + '-' + index" :id="'item-' + gindex + '-' + index">
                            <v-list-item-content>
                                <component
                                    :is="opts.list_item_component"
                                    :options="list_item_options"
                                    :record="rec"
                                    :index="index"
                                    :count="group.records.length"
                                    />
                            </v-list-item-content>
                            <v-list-item-action>
                                <input
                                    class="my-checkbox"
                                    type="checkbox"
                                    :input-value="rec.id"
                                    :true-value="rec.id"
                                    :value="rec.id"
                                    :checked="is_selected(rec)"
                                    @click="handleSelect(rec, $event)"
                                    />
                            </v-list-item-action>
                        </v-list-item>
                        <div class="extra" v-if="opts.list_item_extra_component">
                            <component
                                :is="opts.list_item_extra_component"
                                :options="list_item_options"
                                :record="rec"
                                :index="index"
                                :count="group.records.length"
                                />
                        </div>
                    </div>
                </div>
            </v-list>
            <div class="no-record pa-2" v-if="!has_records">
                <p class="text--secondary">No item to select.</p>
            </div>
        </v-card>
        <v-row class="actions bottom-actions" v-if="has_records && opts.showActions">
            <v-col>
                <v-btn depressed color="success" @click="handleAction('submit')" :disabled="!valued">
                    Confirm
                </v-btn>
            </v-col>
        </v-row>
    </div>
  `,
});
