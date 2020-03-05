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
        bubbleUpAction: {
            'type': Boolean,
            'default': false,
        },
        showActions: {
            'type': Boolean,
            'default': true,
        },
        initSelectAll: {
            'type': Boolean,
            'default': false,
        },
        initValue: {
            'type': [Number, Array],
            'default': null,
        },
        multiple: {
            'type': Boolean,
            'default': false,
        },
    },
    data: function () {
        const self = this;
        let selected;
        if (this.multiple) {
            selected = self.initValue ? [self.initValue] : [];
            if (this.initSelectAll) {
                selected = _.map(this.records, function (x) {
                    return x[self.key_value];
                });
            }
        } else {
            selected = self.initValue ? self.initValue : null;
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
            if (this.bubbleUpAction) {
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
        options () {
            return {
                'key_value': this.key_value,
                'key_title': this.key_title,
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
            if (this.showActions) {
                bits.push('with-bottom-actions');
            }
            if (this.grouped_records.length) {
                bits.push('with-groups');
            }
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
                <v-list-item-group :multiple="multiple || null" color="success" v-model="selected">
                    <div class="select-group" v-for="group in selectable" :key="group.key">
                        <v-card-title v-if="group.title">{{ group.title }}</v-card-title>
                        <v-list-item
                                v-for="rec in group.records"
                                :key="rec[key_value]"
                                :value="rec[key_value]"
                                :data-id="rec[key_value]"
                                >
                            <v-list-item-content>
                                <component :is="list_item_content_component" :options="options" :record="rec"></component>
                            </v-list-item-content>
                        </v-list-item>
                    </div>
                </v-list-item-group>
            </v-list>
            <v-alert tile type="error" v-if="!has_records">
                No record found.
            </v-alert>
        </v-card>
        <v-row class="actions bottom-actions" v-if="has_records && showActions">
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
