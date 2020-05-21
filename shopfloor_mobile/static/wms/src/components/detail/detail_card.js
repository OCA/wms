import {ItemDetailMixin} from "./detail_mixin.js";

Vue.component("item-detail-card", {
    mixins: [ItemDetailMixin],
    props: ["card_color"],
    template: `
    <div :class="wrapper_klass">
        <v-card :color="card_color" tile :class="{'main': opts.main, 'no-outline': opts.no_outline}" v-if="!_.isEmpty(record)">
            <v-card-title v-if="!opts.no_title">
                <slot name="title">
                    <span v-text="_.result(record, opts.key_title)" />
                    <v-btn icon class="detail-action" v-if="opts.on_title_action" @click="opts.on_title_action()">
                        <v-icon color="blue lighten-1">mdi-information</v-icon>
                    </v-btn>
                </slot>
            </v-card-title>
            <v-card-subtitle v-if="$slots.subtitle">
                <slot name="subtitle"></slot>
            </v-card-subtitle>
            <slot name="details">
                <!-- TODO: this loop is the same in list-item => make it a component -->
                <v-card-text class="details" v-if="opts.fields.length">
                    <div v-for="(field, index) in opts.fields" :class="'field-detail ' + field.path.replace('.', '-') + ' ' + (field.klass || '')">
                        <div v-if="raw_value(record, field) || field.display_no_value">
                            <span v-if="field.label" class="label">{{ field.label }}:</span> {{ render_field_value(record, field) }}
                            <v-btn icon class="detail-action"
                                    v-if="has_detail_action(record, field)"
                                    @click="on_detail_action(record, field, opts)">
                                <v-icon color="blue lighten-1">mdi-information</v-icon>
                            </v-btn>
                        </div>
                    </div>
                </v-card-text>
            </slot>
        </v-card>
        <p v-if="_.isEmpty(record)">
            No detail record to display.
        </p>
    </div>
  `,
});
