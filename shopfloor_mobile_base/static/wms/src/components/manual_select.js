/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

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
            const val = isNaN(elem.value) ? elem.value : parseInt(elem.value, 10);
            this._updateValue(val, elem.checked);
            $(elem)
                .closest(".list-item-wrapper")
                .toggleClass(this.selected_color_klass(), elem.checked);
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
        is_disabled(rec) {
            // If value is required and there's no btn to confirm block unselecting the checkbox
            return (
                !this.opts.multiple &&
                !this.opts.showActions &&
                this.opts.required &&
                this.is_selected(rec)
            );
        },
        selected_color_klass(modifier) {
            return (
                "active " +
                this.utils.colors.color_for("item_selected") +
                (modifier ? " " + modifier : "")
            );
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
                key_title: "name",
                show_title: true,
                showActions: true,
                initSelectAll: false,
                initValue: null,
                multiple: false,
                required: false,
                showCounters: false,
                list_item_component: "list-item",
                list_item_actions: [],
                list_item_extra_component: "",
                selected_event: "select",
                group_color: "",
                group_title_default: "",
            });
            return opts;
        },
        list_item_options() {
            const opts = _.defaults({}, this.opts.list_item_options, {
                // TODO: we should not mix up propertes and rely on `list_item_options` inside `options`
                show_title: this.opts.show_title,
                key_title: this.opts.key_title,
                showCounters: this.opts.showCounters,
                fields: this.$props.list_item_fields,
            });
            return opts;
        },
        selectable() {
            if (!this.grouped_records.length) {
                // Simulate grouping (allows to keep template the same)
                return [
                    {
                        key: "no-group",
                        title: this.opts.group_title_default,
                        records: this.records,
                    },
                ];
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
            if (this.grouped_records.length) bits.push("with-groups");
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
        <v-card :class="['select-group', opts.card_klass]"
            :color="group.group_color || opts.group_color"
            v-for="(group, gindex) in selectable"
            :key="make_component_key([$options._componentTag, 'group', gindex])">
            <v-card-title v-if="group.title">{{ group.title }}</v-card-title>
            <v-list v-if="has_records">
                <div :class="['list-item-wrapper', is_selected(rec) ? selected_color_klass() : '']" v-for="(rec, index) in group.records"">
                    <v-list-item :key="make_component_key(['group-rec', gindex, index, rec.id])"
                                :class="list_item_options.list_item_klass_maker ? list_item_options.list_item_klass_maker(rec) : ''">
                        <v-list-item-content>
                            <component
                                :is="opts.list_item_component"
                                :options="list_item_options"
                                :record="rec"
                                :index="index"
                                :count="group.records.length"
                                :key="make_component_key([opts.list_item_component, index, rec.id])"
                                />
                        </v-list-item-content>
                        <v-list-item-action>
                            <div class="action action-select">
                                <v-btn icon x-large rounded>
                                    <input
                                        :class="['sf-checkbox', is_selected(rec) ? selected_color_klass('darken-3') : '']"
                                        type="checkbox"
                                        :input-value="rec.id"
                                        :true-value="rec.id"
                                        :value="rec.id"
                                        :checked="is_selected(rec) ? 'checked' : null"
                                        :disabled="is_disabled(rec) ? 'disabled' : null"
                                        :key="make_component_key(['list-checkbox', index, rec.id])"
                                        @click="handleSelect(rec, $event)"
                                        />
                                </v-btn>
                            </div>
                            <component
                                v-for="(action, action_index) in opts.list_item_actions"
                                :is="action.comp_name"
                                v-if="action.enabled(rec, action)"
                                :options="_.merge({}, list_item_options, action.get_options(rec, action))"
                                :record="action.get_record(rec, action)"
                                :index="index"
                                :count="group.records.length"
                                :key="make_component_key([action.comp_name, index, action_index, rec.id])"
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
                            :key="make_component_key(['list-extra', gindex, index, rec.id])"
                            />
                    </div>
                </div>
            </v-list>
        </v-card>
        <v-card :color="opts.group_color" class="no-record pa-2" v-if="!has_records">
            <!-- Use v-list to have the same look and feel of the record list -->
            <v-list>
                <v-list-item>
                    <v-list-item-content>
                        <p class="secondary--text">{{ $t('select.no_items') }}</p>
                        </v-list-item-content>
                </v-list-item>
            </v-list>
        </v-card>
        <v-row class="actions bottom-actions" v-if="has_records && opts.showActions">
            <v-col>
                <v-btn color="success" @click="handleAction('submit')" :disabled="!valued">
                    {{ $t("btn.confirm.title") }}
                </v-btn>
            </v-col>
        </v-row>
    </div>
  `,
});
