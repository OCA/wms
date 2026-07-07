/**
 * Copyright 2026 ACSONE SA/NV (https://www.acsone.eu/)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("form-edit-product-packaging", {
    props: {
        packaging: {type: Object, required: true},
        allowEditName: {type: Boolean, default: false},
        showCancel: {type: Boolean, default: false},
    },
    created: function () {
        this.prefill_packaging_form_inputs();
    },
    template: `
<div v-if="packaging">
    <item-detail-card
        :record="packaging"
        :options="packaging_detail_options()"
    />

    <v-form ref="form_dimension">
        <v-container>
            <v-row v-if="allowEditName">
                <v-text-field
                    label="Name"
                    placeholder="Name"
                    v-model="packaging.name_input"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Barcode"
                    placeholder="Packaging Barcode"
                    v-model="packaging.barcode_input"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Quantity"
                    type="number"
                    placeholder="Packaging Quantity"
                    v-model="packaging.qty_input"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Length"
                    type="number"
                    :suffix="packaging.length_uom_name"
                    placeholder="Packaging Length"
                    v-model="packaging.packaging_length_input"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Width"
                    type="number"
                    :suffix="packaging.length_uom_name"
                    placeholder="Packaging Width"
                    v-model="packaging.width_input"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Height"
                    type="number"
                    :suffix="packaging.length_uom_name"
                    placeholder="Packaging Height"
                    v-model="packaging.height_input"
                ></v-text-field>
            </v-row>
            <v-row>
                <v-text-field
                    label="Weight"
                    type="number"
                    :suffix="packaging.weight_uom_name"
                    placeholder="Packaging Weight"
                    v-model="packaging.weight_input"
                ></v-text-field>
            </v-row>
        </v-container>
    </v-form>

    <div class="button-list button-vertical-list full">
        <v-row align="center">
            <v-col class="text-center" cols="12">
                <btn-action @click="on_done">Done</btn-action>
            </v-col>
        </v-row>
        <v-row align="center" v-if="!showCancel">
            <v-col class="text-center" cols="12">
                <btn-action color="default" @click="on_skip">Skip</btn-action>
            </v-col>
        </v-row>
        <v-row align="center" v-if="showCancel">
            <v-col class="text-center" cols="12">
                <btn-action color="error" @click="on_cancel">Cancel</btn-action>
            </v-col>
        </v-row>
    </div>
</div>
`,
    methods: {
        on_done: function () {
            this.$emit("done", {
                name: this.packaging.name_input,
                packaging_length: this.packaging.packaging_length_input,
                width: this.packaging.width_input,
                height: this.packaging.height_input,
                weight: this.packaging.weight_input,
                qty: this.packaging.qty_input,
                barcode: this.packaging.barcode_input,
            });
        },
        on_skip: function () {
            this.$emit("skip");
        },
        on_cancel: function () {
            this.$emit("cancel");
        },
        prefill_packaging_form_inputs: function () {
            const pkg = this.packaging;
            const input_fields = this.get_packaging_measurements_inputs();

            input_fields.forEach((inputKey) => {
                const originalKey = inputKey.replace("_input", "");
                if (pkg[inputKey] === undefined || pkg[inputKey] === null) {
                    this.$set(pkg, inputKey, pkg[originalKey]);
                }
            });
        },
        get_packaging_measurements_inputs: function () {
            return [
                "name_input",
                "packaging_length_input",
                "width_input",
                "height_input",
                "weight_input",
                "qty_input",
                "barcode_input",
            ];
        },
        packaging_detail_options: function () {
            const pkg = this.packaging;
            const _is_field_changed = (fieldName) => {
                const inputKey = fieldName + "_input";
                return pkg[inputKey] && pkg[inputKey] != pkg[fieldName];
            };
            const options = {
                main: true,
                key_title: "name",
                title_icon: "mdi-package-variant",
                fields: [
                    {
                        path: "name",
                        label: "Name",
                        klass: _is_field_changed("name") ? "accent" : "",
                    },
                    {
                        path: "barcode",
                        label: "Barcode",
                        klass: _is_field_changed("barcode") ? "accent" : "",
                    },
                    {
                        path: "qty",
                        label: "Quantity",
                        klass: _is_field_changed("qty") ? "accent" : "",
                    },
                    {
                        path: "packaging_length",
                        label: "Length",
                        klass: _is_field_changed("packaging_length") ? "accent" : "",
                        renderer: function (rec, field) {
                            const value = _.result(rec, "packaging_length", "");
                            const uom = _.result(rec, "length_uom_name", "");
                            return value + " " + uom;
                        },
                    },
                    {
                        path: "width",
                        label: "Width",
                        klass: _is_field_changed("width") ? "accent" : "",
                        renderer: function (rec, field) {
                            const value = _.result(rec, "width", "");
                            const uom = _.result(rec, "length_uom_name", "");
                            return value + " " + uom;
                        },
                    },
                    {
                        path: "height",
                        label: "Height",
                        klass: _is_field_changed("height") ? "accent" : "",
                        renderer: function (rec, field) {
                            const value = _.result(rec, "height", "");
                            const uom = _.result(rec, "length_uom_name", "");
                            return value + " " + uom;
                        },
                    },
                    {
                        path: "weight",
                        label: "Weight",
                        klass: _is_field_changed("weight") ? "accent" : "",
                        renderer: function (rec, field) {
                            const value = _.result(rec, "weight", "");
                            const uom = _.result(rec, "weight_uom_name", "");
                            return value + " " + uom;
                        },
                    },
                ],
            };
            return options;
        },
    },
});
