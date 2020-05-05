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

            {path: "field.subfield", label: "Line count"},

        Path is the dotted path to the field value.
        Label is optional and if not provided only the value will be shown.

        Override this in your custom component or via options.
        */
        detail_fields() {
            return [];
        },
    },
    computed: {
        wrapper_klass: function() {
            return [
                "detail",
                this.$options._componentTag,
                this.opts.loud ? "loud" : "",
                this.opts.klass || "",
            ].join(" ");
        },
        opts() {
            // Defining defaults for an Object property
            // works only if you don't pass the property at all.
            // If you pass only one key, you'll lose all defaults.
            const opts = _.defaults({}, this.$props.options, {
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
