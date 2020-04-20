/* eslint-disable strict */
Vue.component("manual-select", {
    props: {
        records: {
            type: Array,
            default: [],
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
    },
    data: function() {
        return {
            selected: null,
        };
    },
    created() {
        // Relies on properties
        this.selected = this._initSelected();
    },
    methods: {
        _initSelected() {
            const initValue = this.opts.initValue;
            let selected = null;
            if (this.opts.multiple) {
                selected = initValue ? [initValue] : [];
                if (this.opts.initSelectAll) {
                    selected = [];
                    _.each(this.records, function(rec, index) {
                        selected.push(index);
                    });
                }
            } else {
                selected = initValue ? initValue : null;
            }
            return selected;
        },
        handleAction(event_name, data) {
            // TODO: use `$root.trigger` and replace handling of select event
            // everywhere.
            if (this.opts.bubbleUpAction) {
                this.$parent.$emit(event_name, data);
            } else {
                this.$emit(event_name, data);
            }
        },
    },
    watch: {
        // eslint-disable-next-line no-unused-vars
        selected: function(val, oldVal) {
            if (_.isUndefined(val)) {
                // Unselected
                this.handleAction("select", null);
                return;
            }
            const self = this;
            let selected_records = null;
            if (this.opts.multiple) {
                selected_records = [];
                _.each(this.records, function(rec, index) {
                    if (index in val) selected_records.push(rec);
                });
            } else {
                selected_records = self.records[val];
            }
            console.log("SELECTED", selected_records);
            if (!this.opts.showActions) {
                // Bubble up select action (handy when no action used)
                this.handleAction("select", selected_records);
            }
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
                bubbleUpAction: false,
                showActions: true,
                initSelectAll: false,
                initValue: null,
                multiple: false,
                showCounters: false,
                list_item_component: "list-item",
                list_item_extra_component: "",
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
    },
    template: `
    <div :class="klass">
        <v-card outlined>
            <v-list v-if="has_records">
                <v-list-item-group :multiple="opts.multiple" color="success" v-model="selected">
                    <div class="select-group" v-for="group in selectable" :key="group.key">
                        <v-card-title v-if="group.title">{{ group.title }}</v-card-title>
                        <div class="list-item-wrapper" v-for="(rec, index) in group.records"">
                            <v-list-item :key="index">
                                <template v-slot:default="{ active, toggle }">
                                    <v-list-item-content>
                                        <component
                                            :is="opts.list_item_component"
                                            :options="list_item_options"
                                            :record="rec"
                                            :index="index"
                                            :count="group.records.length"
                                            />
                                    </v-list-item-content>
                                    <!--v-list-item-action>
                                     FIXME: this triggers the change 3 times and makes impossible to handle event subscribers properly
                                        <v-checkbox
                                            :input-value="active"
                                            :true-value="index"
                                            color="accent-4"
                                            @click="toggle"
                                        ></v-checkbox>
                                    </v-list-item-action-->
                                </template>
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
                </v-list-item-group>
            </v-list>
            <v-alert tile type="error" v-if="!has_records">
                No record found.
            </v-alert>
        </v-card>
        <v-row class="actions bottom-actions" v-if="has_records && opts.showActions">
            <v-col>
                <v-btn depressed color="success" @click="handleAction('select', selected)">
                    Start
                </v-btn>
            </v-col>
            <v-col>
                <v-btn depressed color="default" @click="handleAction('back')" class="float-right">
                    Back
                </v-btn>
            </v-col>
        </v-row>
    </div>
  `,
});
