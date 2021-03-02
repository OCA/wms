/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

/* eslint-disable strict */
Vue.component("list", {
    // TODO: move most of this stuff to a mixin and reuse it in manual-select
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
    computed: {
        has_records() {
            return this.records.length > 0;
        },
        listable() {
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
        opts() {
            // Defining defaults for an Object property
            // works only if you don't pass the property at all.
            // If you pass only one key, you'll lose all defaults.
            const opts = _.defaults({}, this.$props.options, {
                showCounters: false,
                key_title: "name",
                show_title: true,
                list_item_component: "list-item",
                list_item_actions: [],
                list_item_on_click: null,
                list_item_options: {},
                group_title_default: "",
                no_divider: false,
            });
            return opts;
        },
        list_item_options() {
            const opts = _.defaults({}, this.opts.list_item_options, {
                key_title: this.opts.key_title,
                loud_title: false,
                showCounters: this.opts.showCounters,
                // customize fields
                fields: this.opts.list_item_fields,
            });
            return opts;
        },
        klass() {
            const bits = ["list"];
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
        <v-card :class="['list-group', opts.card_klass]"
                v-for="(group, gindex) in listable" :key="make_component_key([$options._componentTag, 'group', gindex])"
                :color="group.group_color || opts.group_color">
            <v-card-title v-if="group.title">{{ group.title }}</v-card-title>
            <v-list v-if="has_records">
                <div class="list-item-wrapper" v-for="(rec, index) in group.records">
                    <v-divider
                        v-if="!opts.no_divider && index != 0"
                        :key="make_component_key(['divider', gindex, index, rec.id])"
                        :inset="true" />
                    <v-list-item :key="make_component_key(['group-rec', gindex, index, rec.id])"
                                 :class="list_item_options.list_item_klass_maker ? list_item_options.list_item_klass_maker(rec) : ''"
                                 @click="opts.list_item_on_click ? opts.list_item_on_click(rec) : undefined"
                                 inactive>
                        <v-list-item-content>
                            <component
                                :is="opts.list_item_component"
                                :options="list_item_options"
                                :record="rec"
                                :index="index"
                                :count="group.records.length"
                                :key="make_component_key([opts.list_item_component, 'list', index, rec.id])"
                                />
                        </v-list-item-content>
                        <v-list-item-action v-if="opts.list_item_actions.length">
                            <component
                                v-for="action in opts.list_item_actions"
                                :is="action.comp_name"
                                v-if="action.enabled(rec, action)"
                                :options="_.merge({}, list_item_options, action.get_options(rec, action))"
                                :record="action.get_record(rec, action)"
                                :index="index"
                                :count="group.records.length"
                                :key="make_component_key([action.comp_name, 'list', index, action.get_record(rec, action).id])"
                                />
                        </v-list-item-action>
                    </v-list-item>
                </div>
            </v-list>
            <v-list v-if="!has_records">
                <v-list-item>
                    <v-list-item-content>
                        <p class="secondary--text">{{ $t('list.no_items') }}</p>
                    </v-list-item-content>
                </v-list-item>
            </v-list>
        </v-card>
    </div>
  `,
});

Vue.component("list-item", {
    mixins: [ItemDetailMixin],
    template: `
    <div class="list-item">
        <v-list-item-title v-if="opts.show_title" :class="{'font-weight-bold mb-2': opts.loud_title}">
            <div class="item-counter" v-if="opts.showCounters">
                <span>{{ index + 1 }} / {{ count }}</span>
            </div>
            <span v-text="_.result(record, opts.key_title)" />
        </v-list-item-title>
        <div class="details">
            <div v-for="(field, index) in options.fields" :class="'field-detail ' + field.path.replace('.', '-') + ' ' + (field.klass || '')">
                <span v-if="raw_value(record, field) || field.display_no_value">
                    <span v-if="field.label" class="label">{{ field.label }}:</span>
                    <component
                        v-if="field.render_component"
                        :is="field.render_component"
                        :options="field.render_options ? field.render_options(record) : {}"
                        :record="record"
                        :key="make_component_key([field.render_component, 'list', index, record.id])"
                        />
                    <span v-else>
                        {{ render_field_value(record, field) }}
                    </span>
                </span>
                <v-btn icon class="detail-action"
                        v-if="has_detail_action(record, field)"
                        @click="on_detail_action(record, field, opts)">
                    <btn-info-icon />
                </v-btn>
            </div>
        </div>
    </div>
  `,
});
