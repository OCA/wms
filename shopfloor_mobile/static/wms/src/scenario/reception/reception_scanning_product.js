/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("reception-scanning-product", {
    props: ["stateData"],
    methods: {
        constructDataFromLines: function(moveLines, done) {
            const products = moveLines.reduce((acc, line) => {
                acc[line.product.id] = acc[line.product.id] || {
                    name: line.product.display_name,
                    dest: line.location_dest.name,
                    qtyDone: 0,
                    done,
                };

                acc[line.product.id].qtyDone += line.qty_done;

                return acc;
            }, {});

            return Object.values(products);
        },
        splitMoveLinesByDest: function(moveLines, done) {
            const products = moveLines.reduce((acc, line) => {
                acc[line.product.id + "," + line.location_dest.id] = acc[
                    line.product.id + "," + line.location_dest.id
                ] || {
                    name: line.product.display_name,
                    dest: line.location_dest.name,
                    qtyDone: 0,
                    done,
                };

                acc[line.product.id + "," + line.location_dest.id].qtyDone +=
                    line.qty_done;

                return acc;
            }, {});

            return Object.values(products);
        },
    },
    computed: {
        moveLinesPicked: function() {
            const moveLines = this.stateData.data.move_lines_picked;
            const moveLineByDest = this.splitMoveLinesByDest(moveLines, true);

            return moveLineByDest;
        },
        moveLinesPicking: function() {
            const moveLines = this.stateData.data.move_lines_picking;

            return this.constructDataFromLines(moveLines);
        },
        moveLinesPickingDest: function() {
            return this.stateData.data.move_lines_picking[0].location_dest;
        },
    },
    template: `
        <div>
            <searchbar
                :input_placeholder="scan_placeholder"
                v-on="$listeners"
                />
            <v-row>
                <v-col v-if="moveLinesPicking.length == 0">
                    Start scanning product to start receiving
                </v-col>
            </v-row>
            <reception-product-list
                :fields="stateData.pickingFields"
                :products="moveLinesPicking"
                />
            <v-row>
                <v-col v-if="moveLinesPicking.length > 0">
                    This product should be put in {{moveLinesPickingDest.name}} ({{moveLinesPickingDest.barcode}})
                </v-col>
            </v-row>
            <reception-product-list
                :fields="stateData.pickedFields"
                :products="moveLinesPicked"
                />
        </div>
    `,
    data: () => ({
        scan_placeholder: "Scan product",
    }),
});
