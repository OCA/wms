export var GlobalMixin = {
    methods: {
        /*
        Try to make unique component keys.

        Includes tha parent key by default.
        */
        make_component_key: function(bits) {
            const parent_key = _.result(this.$parent, "$options._componentTag", "");
            if (parent_key) bits.unshift(parent_key + "-");
            bits.unshift(this.$options._componentTag);
            return bits.join("-");
        },
    },
};
