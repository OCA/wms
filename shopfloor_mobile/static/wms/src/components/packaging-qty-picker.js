/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * Copyright 2021 Jacques-Etienne Baudoux (BCIM)
 * @author Jacques-Etienne Baudoux <je@bcim.be>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

export var PackagingQtyPickerMixin = {
    props: {
        options: Object, // options are replaced by props
        mode: String,
        qtyInit: Number,
        uom: {type: Object, required: true},
        availablePackaging: Array,
        pkgNameKey: String, // "code" or "name"
    },
    data: function () {
        return {
            qty: parseInt(this.qtyInit, 10),
            qty_by_pkg: {},
            qty_by_pkg_manual: false,
        };
    },
    watch: {
        qtyInit: function () {
            this.qty = parseInt(this.qtyInit, 10);
        },
        qty: {
            handler() {
                if (!this.qty_by_pkg_manual) {
                    this.qty_by_pkg = this.product_qty_by_packaging();
                }
                this.qty_by_pkg_manual = false;
            },
            immediate: true,
        },
    },
    methods: {
        _handle_qty_error(event, input, new_qty) {
            event.preventDefault();
            // Make it red and shake it
            $(input)
                .closest(".inner-wrapper")
                .addClass("error shake-it")
                .delay(800)
                .queue(function () {
                    // End animation
                    $(this)
                        .removeClass("error shake-it", 2000, "easeInOutQuad")
                        .dequeue();
                    // Restore value
                    $(input).val(new_qty);
                });
        },
        packaging_by_id: function (id) {
            // Special case for UOM ids as they can clash w/ pkg ids
            // we prefix it w/ "uom-"
            id = id.startsWith("uom-") ? id : parseInt(id, 10);
            return _.find(this.sorted_packaging, ["id", id]);
        },
        /**
         *
        Calculate quantity by packaging.

        Limitation: fractional quantities are lost.

        :prod_qty:
        :min_unit: minimal unit of measure as a tuple (qty, name).
                   Default: to UoM unit.
        :returns: list of tuple in the form [(qty_per_package, package_name)]

         * @param {*} prod_qty total qty to satisfy.
         * @param {*} min_unit minimal unit of measure as a tuple (qty, name).
                   Default: to UoM unit.
        */
        product_qty_by_packaging: function () {
            return this._product_qty_by_packaging(this.sorted_packaging, this.qty);
        },
        /**
         * Produce a list of tuple of packaging qty and packaging name.
         * TODO: refactor to handle fractional quantities (eg: 0.5 Kg)
         *
         * @param {*} pkg_by_qty packaging records sorted by major qty
         * @param {*} qty total qty to satisfy
         */
        _product_qty_by_packaging: function (pkg_by_qty, qty) {
            const self = this;
            const res = {};
            // Const min_unit = _.last(pkg_by_qty);
            pkg_by_qty.forEach(function (pkg) {
                let qty_per_pkg = 0;
                [qty_per_pkg, qty] = self._qty_by_pkg(pkg.qty, qty);
                res[pkg.id] = qty_per_pkg;
                if (!qty) return;
            });
            return res;
        },
        /**
         * Calculate qty needed for given package qty.
         *
         * @param {*} pkg_by_qty
         * @param {*} qty
         */
        _qty_by_pkg: function (pkg_qty, qty) {
            const precision = this.unit_uom.rounding || 3;
            let qty_per_pkg = 0;
            // TODO: anything better to do like `float_compare`?
            while (_.round(qty - pkg_qty, precision) >= 0.0) {
                qty -= pkg_qty;
                qty_per_pkg += 1;
            }
            return [qty_per_pkg, qty];
        },
        _compute_qty: function () {
            const self = this;
            let value = 0;
            _.forEach(this.qty_by_pkg, function (qty, id) {
                value += self.packaging_by_id(id).qty * qty;
            });
            return value;
        },
        compute_qty: function () {
            this.qty = this._compute_qty();
        },
    },
    computed: {
        unit_uom: function () {
            let unit = {};
            if (!_.isEmpty(this.uom)) {
                // Create an object like the packaging
                // to be used seamlessly in the widget.
                unit = {
                    id: "uom-" + this.uom.id,
                    name: this.uom.name,
                    qty: this.uom.factor,
                    rounding: this.uom.rounding,
                };
            }
            return unit;
        },
        /**
         * Sort packaging by qty and exclude the ones w/ qty = 0
         * Include the uom
         */
        sorted_packaging: function () {
            let packagings = _.reverse(
                _.sortBy(
                    _.filter(this.availablePackaging, _.property("qty")),
                    _.property("qty")
                )
            );
            let unit = [];
            if (!_.isEmpty(this.unit_uom)) {
                unit = [this.unit_uom];
            }
            return _.concat(packagings, unit);
        },
        /**
         * Collect qty of contained packaging inside bigger packaging.
         * Eg: "1 Pallet" contains "4 Big boxes".
         */
        contained_packaging: function () {
            const self = this;
            let res = {},
                qty_per_pkg,
                remaining,
                elected_next_pkg;
            const packaging = this.sorted_packaging;
            _.forEach(packaging, function (pkg, i) {
                const next_pkgs = packaging.slice(i + 1);
                remaining = undefined;
                _.every(next_pkgs, function (next_pkg) {
                    [qty_per_pkg, remaining] = self._qty_by_pkg(next_pkg.qty, pkg.qty);
                    elected_next_pkg = next_pkg;
                    return remaining;
                });
                if (remaining === 0) {
                    res[pkg.id] = {
                        pkg: elected_next_pkg,
                        qty: qty_per_pkg,
                    };
                }
            });
            return res;
        },
    },
};

export var PackagingQtyPicker = Vue.component("packaging-qty-picker", {
    mixins: [PackagingQtyPickerMixin],
    props: {
        readonly: Boolean,
        qtyTodo: {type: Number, required: true},
        pkgNameKey: {default: "name"},
    },
    data: function () {
        return {
            panel: 0, // expand panel by default
        };
    },
    watch: {
        qty_by_pkg: {
            deep: true,
            handler: function () {
                // prevent watched qty to update again qty_by_pkg
                this.qty_by_pkg_manual = true;
                this.compute_qty();
                this.qty_by_pkg_manual = false;
            },
        },
    },
    created: function () {
        // Propagate the newly initialized quantity to the parent component
        this.$root.trigger("qty_edit", this.qty);
    },
    updated: function () {
        this.$root.trigger("qty_edit", this.qty);
    },
    computed: {
        qty_color: function () {
            if (this.qty == this.qtyTodo) {
                if (this.readonly) return "";
                return "background-color: rgb(143, 191, 68)";
            }
            if (this.qty > this.qtyTodo) {
                return "background-color: orangered";
            }
            return "background-color: pink";
        },
        qty_todo_by_pkg: function () {
            // Used to calculate the qty needed of each package type
            // based on the qty todo.
            let total_qty_todo = this.qtyTodo;
            const res = {};
            this.sorted_packaging.forEach((pkg) => {
                let pkg_units = 0;
                while (pkg.qty <= total_qty_todo) {
                    pkg_units++;
                    total_qty_todo -= pkg.qty;
                }
                res[pkg.id] = pkg_units;
            });
            return res;
        },
    },
    template: `
<div :class="[$options._componentTag, mode ? 'mode-' + mode : '']">
    <v-expansion-panels flat v-model="panel">
        <v-expansion-panel>
            <v-expansion-panel-header expand-icon="mdi-menu-down">
                <v-row dense align="center">
                    <v-col cols="5" md="3">
                        <input type="number" v-model="qty" class="qty-done" :style="qty_color"
                            v-on:click.stop
                            :readonly="readonly"
                        />
                    </v-col>
                    <v-col cols="3" md="2" v-if="!readonly">
                        <span class="qty-todo">/ {{ qtyTodo }}</span>
                    </v-col>
                    <v-col>
                        {{ unit_uom.name }}
                    </v-col>
                </v-row>
            </v-expansion-panel-header>
            <v-expansion-panel-content v-if="sorted_packaging.length > 1">
                <v-row dense
                    align="center"
                    v-for="(pkg, index) in sorted_packaging"
                    :key="make_component_key([pkg.id])"
                    :class="(readonly && !qty_by_pkg[pkg.id]) ? 'd-none' : ''"
                >
                    <v-col cols="4" md="2">
                        <input type="text" inputmode="decimal" class="qty-done"
                            v-model.lazy="qty_by_pkg[pkg.id]"
                            :data-origvalue="qty_by_pkg[pkg.id]"
                            :data-pkg="JSON.stringify(pkg)"
                            :readonly="readonly"
                            @focus="!readonly && ($event.target.value='')"
                            @blur="$event.target.value=qty_by_pkg[pkg.id]"
                            />
                    </v-col>
                    <v-col cols="2" md="2" v-if="!readonly">
                        <span class="qty-todo">/ {{ qty_todo_by_pkg[pkg.id] }}</span>
                    </v-col>
                    <v-col>
                        <div class="pkg-name"> {{ pkg[pkgNameKey] }}</div>
                        <div v-if="contained_packaging[pkg.id]" class="pkg-qty">(x{{ contained_packaging[pkg.id].qty }} {{ contained_packaging[pkg.id].pkg.name }})</div>
                    </v-col>
                </v-row>
            </v-expansion-panel-content>
        </v-expansion-panel>
    </v-expansion-panels>
</div>
`,
});

export var PackagingQtyPickerDisplay = Vue.component("packaging-qty-picker-display", {
    mixins: [PackagingQtyPickerMixin],
    props: {
        nonZeroOnly: Boolean,
        pkgNameKey: {default: "code"},
    },
    methods: {
        display_pkg: function (pkg) {
            return this.nonZeroOnly ? this.qty_by_pkg[pkg.id] > 0 : true;
        },
    },
    computed: {
        visible_packaging: function () {
            let packagings = _.filter(this.sorted_packaging, this.display_pkg);
            // Do not display if only uom packaging
            if (
                packagings.length == 1 &&
                packagings[0].id.toString().startsWith("uom-")
            )
                return [];
            return packagings;
        },
    },
    template: `
    <div :class="[$options._componentTag, mode ? 'mode-' + mode: '', 'd-inline']">
        <span class="min-unit">{{ qty }} {{ unit_uom.name }}</span>
        <span class="packaging" v-for="(pkg, index) in visible_packaging" :key="make_component_key([pkg.id])">
            <span v-if="index == 0">(</span>
            <span class="pkg-qty" v-text="qty_by_pkg[pkg.id]" />
            <span class="pkg-name" v-text="pkg[pkgNameKey] || unit_uom.name" /><span class="sep" v-if="index != Object.keys(visible_packaging).length - 1"> + </span>
            <span v-if="index == visible_packaging.length - 1">)</span>
        </span>
    </div>
`,
});
