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
            default: function() {
                return {
                    bubbleUpAction: false,
                    showActions: true,
                    initSelectAll: false,
                    initValue: null,
                    multiple: false,
                    showCounters: false,
                    list_item_component: "manual-select-item",
                    list_item_extra_component: "",
                };
            },
        },
        list_item_fields: {
            type: Array,
            default: function() {
                return [];
            },
        },
    },
    data: function() {
        const self = this;
        const initValue = this.options.initValue;
        let selected = null;
        if (this.options.multiple) {
            selected = initValue ? [initValue] : [];
            if (this.options.initSelectAll) {
                selected = _.map(this.records, function(x) {
                    return self.records.indexOf(x);
                });
            }
        } else {
            selected = initValue ? initValue : null;
        }
        return {
            selected: selected,
        };
    },
    methods: {
        handleAction(event_name, data) {
            // TODO: any better way to handle this?
            // We want to be able to hook to the action
            // on grand-parent components as well.
            // Maybe we can emit the event on the $root
            // and add a namespace to the event (eg: usage:event_name)
            if (this.options.bubbleUpAction) {
                this.$parent.$emit(event_name, data);
            } else {
                this.$emit(event_name, data);
            }
        },
    },
    watch: {
        // eslint-disable-next-line no-unused-vars
        selected: function(val, oldVal) {
            const self = this;
            // Bubble up select action (handy when no action used)
            const selected_records = _.pickBy(this.records, function(x) {
                return self.records.indexOf(x) === val;
            });
            this.handleAction("select", selected_records);
        },
    },
    computed: {
        has_records() {
            return this.records.length > 0;
        },
        list_item_options() {
            return {
                key_title: this.key_title,
                showCounters: this.options.showCounters,
                fields: this.list_item_fields,
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
            _.forEach(this.$props.options, function(v, k) {
                if (v) {
                    bits.push("with-" + k);
                }
            });
            return bits.join(" ");
        },
    },
    template: `
    <div :class="klass">
        <v-card outlined>
            <v-list v-if="has_records">
                <v-list-item-group :multiple="options.multiple" color="success" v-model="selected">
                    <div class="select-group" v-for="group in selectable" :key="group.key">
                        <v-card-title v-if="group.title">{{ group.title }}</v-card-title>
                        <div class="list-item-wrapper" v-for="(rec, index) in group.records"">
                            <v-list-item :key="index">
                                <template v-slot:default="{ active, toggle }">
                                    <v-list-item-content>
                                        <component
                                            :is="options.list_item_component"
                                            :options="list_item_options"
                                            :record="rec"
                                            :index="index"
                                            :count="group.records.length"
                                            />
                                    </v-list-item-content>
                                    <v-list-item-action>
                                        <v-checkbox
                                            :input-value="active"
                                            :true-value="index"
                                            color="accent-4"
                                            @click="toggle"
                                        ></v-checkbox>
                                    </v-list-item-action>
                                </template>
                            </v-list-item>
                            <div class="extra" v-if="options.list_item_extra_component">
                                <component
                                    :is="options.list_item_extra_component"
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
        <v-row class="actions bottom-actions" v-if="has_records && options.showActions">
            <v-col>
                <v-btn color="success" @click="handleAction('select', selected)">
                    Start
                </v-btn>
            </v-col>
            <v-col>
                <v-btn color="default" @click="handleAction('back')" class="float-right">
                    Back
                </v-btn>
            </v-col>
        </v-row>
    </div>
  `,
});

// TODO: this could be use for display detail as well
Vue.component("manual-select-item", {
    props: {
        record: Object,
        options: Object,
    },
    methods: {
        render_field_value(record, field) {
            console.log(field);
            if (field.renderer) {
                return field.renderer(record);
            }
            return _.result(record, field.path);
        },
    },
    template: `
    <div>
        <v-list-item-title v-text="record[options.key_title]"></v-list-item-title>
        <div class="details">
            <div class="field-detail" v-for="(field, index) in options.fields">
                <span v-if="field.label" class="label">{{ field.label }}:</span> {{ render_field_value(record, field) }}
            </div>
        </div>
    </div>
  `,
});
