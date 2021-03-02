/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

export var ItemDetailMixin = {
    props: {
        record: Object,
        options: Object,
        klass: String,
    },
    methods: {
        // TODO: document. Current reference on usage: list-item component
        render_field_value(record, field) {
            if (field.renderer) {
                return field.renderer(record, field);
            }
            return this.raw_value(record, field);
        },
        raw_value(record, field) {
            return _.result(record, field.path);
        },
        /*
        List of fields' description in the format:

            {
                // lodash.result path like value
                path: "field.subfield",
                // use a lable for the field if present
                label: "Line count",
                // add extra class to field wrapper
                klass: "foo",
                // lodash.result path like value for an action
                // (eg: product.barcode)
                action_val_path
            },

        Path is the dotted path to the field value.
        Label is optional and if not provided only the value will be shown.

        Override this in your custom component or via options.
        */
        detail_fields() {
            return [];
        },
        _render_date(record, field) {
            return this.utils.display.format_date_display(_.result(record, field.path));
        },
        has_detail_action(record, field) {
            return _.result(record, field.action_val_path);
        },
        on_detail_action(record, field, options = {}) {
            let handler = this.default_detail_action_handler;
            handler = field.detail_action
                ? field.detail_action
                : options.detail_action || handler;
            handler.call(this, record, field);
        },
        default_detail_action_handler(record, field) {
            const identifier = _.result(record, field.action_val_path);
            if (identifier) {
                // TODO: we should probably delegate this to a global event
                this.$router.push({
                    name: "scan_anything",
                    params: {identifier: identifier},
                    query: {displayOnly: 1},
                });
            } else {
                console.error("Action handler found not value for", field);
            }
        },
    },
    computed: {
        wrapper_klass: function() {
            return [
                "detail",
                this.$options._componentTag,
                this.opts.loud ? "loud" : "",
                this.opts.loud_labels ? "loud-labels" : "",
                this.opts.klass || "",
            ].join(" ");
        },
        opts() {
            // Defining defaults for an Object property
            // works only if you don't pass the property at all.
            // If you pass only one key, you'll lose all defaults.
            const opts = _.defaults({}, this.$props.options, {
                no_title: false,
                key_title: "name",
                fields: this.detail_fields(),
                full_detail: false,
                // customize action per all detail fields
                detail_action: null,
            });
            return opts;
        },
    },
};
