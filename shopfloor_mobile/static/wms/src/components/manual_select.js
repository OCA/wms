Vue.component('manual-select', {
    props: {
        'records': {
            'type': Array,
            'default': [],
        },
        'key_value': {
            'type': String,
        },
        'key_title': {
            'type': String,
            'default': 'name',
        },
        'list_item_content_component': {
            'type': String,
        },
        'grouped': {
            'type': Boolean,
            'default': false,
        },
        'bubbleUpAction': {
            'type': Boolean,
            'default': false,
        },
        'eventFullRecord': {
            'type': Boolean,
            'default': false,
        },
    },
    data: function () {
        return {'selected': null};
    },
    methods: {
        // NOTE: v-list-item-group should be able to work w/ `v-model`.
        // For some reason, it does not work here.
        // At the same time is preferable to have a place to hook to
        // in case you want to customize its behavior.
        updateSelected (selectedItem) {
            this.selected = selectedItem;
        },
        // TODO: any better way to handle this?
        // We want to be able to hook to the action
        // on grand-parent components as well
        handleAction (event_name, data) {
            if (this.bubbleUpAction) {
                this.$parent.$emit(event_name, data);
            } else {
                this.$emit(event_name, data);
            }
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
            if (!this.grouped) {
                // Simulate grouping (allows to keep template the same)
                return [
                    {'key': 'no-group', 'title': '', 'records': this.records},
                ];
            }
            return this.records;

        },
    },
    mounted: function () {
        if (this.records.length && !this.selected) {
            this.updateSelected(this.records[0][this.key_value]);
        }
    },
    template: `
    <div :class="'manual-select with-bottom-actions ' + (grouped ? 'with-groups' : '' )">
        <v-card outlined>
            <v-list shaped v-if="has_records">
                <v-list-item-group mandatory color="success">
                    <div class="select-group" v-for="group in selectable" :key="group.key">
                        <v-list-item-title v-if="group.title">{{ group.title }}</v-list-item-title>
                        <v-list-item
                                v-for="rec in group.records"
                                :key="rec[key_value]"
                                :data-id="rec[key_value]"
                                @click="updateSelected(rec[key_value])"
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
        <v-row class="actions bottom-actions" v-if="has_records">
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
