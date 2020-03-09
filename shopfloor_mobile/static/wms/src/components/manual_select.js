Vue.component('manual-select', {
    props: {
        records: {
            'type': Array,
            'default': [],
        },
        grouped_records: {
            'type': Array,
            'default': [],
        },
        key_value: {
            'type': String,
        },
        key_title: {
            'type': String,
            'default': 'name',
        },
        list_item_content_component: {
            'type': String,
        },
        options: {
            'type': Object,
            'default': function () {
                return {
                    bubbleUpAction: false,
                    showActions: true,
                    initSelectAll: false,
                    initValue: null,
                    multiple: false,
                    showCounters: false,
                };
            },
        },
    },
    data: function () {
        const self = this;
        const initValue = this.options.initValue;
        let selected;
        if (this.options.multiple) {
            selected = initValue ? [initValue] : [];
            if (this.options.initSelectAll) {
                selected = _.map(this.records, function (x) {
                    return x[self.key_value];
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
        handleAction (event_name, data) {
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
        selected: function (val, oldVal) {
            // Bubble up select action (handy when no action used)
            this.handleAction('select', this.selected);
        },
    },
    computed: {
        has_records () {
            return this.records.length > 0;
        },
        list_item_options () {
            return {
                'key_value': this.key_value,
                'key_title': this.key_title,
                'showCounters': this.options.showCounters,
            };
        },
        selectable () {
            if (!this.grouped_records.length) {
                // Simulate grouping (allows to keep template the same)
                return [
                    {'key': 'no-group', 'title': '', 'records': this.records},
                ];
            }
            return this.grouped_records;

        },
        klass () {
            const bits = ["manual-select"];
            _.forEach(this.$props.options, function (v, k) {
                if (v) {
                    bits.push('with-' + k);
                }
            });
            return bits.join(' ');
        },
    },
    // Mounted: function () {
    //     if (this.records.length && !this.selected) {
    //         this.updateSelected(this.records[0][this.key_value]);
    //     }
    // },
    template: `
    <div :class="klass">
        <v-card outlined>
            <v-list shaped v-if="has_records">
                <v-list-item-group :multiple="options.multiple" color="success" v-model="selected">
                    <div class="select-group" v-for="group in selectable" :key="group.key">
                        <v-card-title v-if="group.title">{{ group.title }}</v-card-title>
                        <v-list-item
                                v-for="(rec, index) in group.records"
                                :key="rec[key_value]"
                                :value="rec[key_value]"
                                :data-id="rec[key_value]"
                                >
                            <v-list-item-content>
                                <component
                                    :is="list_item_content_component"
                                    :options="list_item_options"
                                    :record="rec"
                                    :index="index"
                                    :count="group.records.length"
                                    ></component>
                            </v-list-item-content>
                        </v-list-item>
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
