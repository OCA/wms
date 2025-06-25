/**
 * Copyright 2025 ACSONE SA/NV (https://acsone.eu)
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

/*
 * This is a component in order to display the destination location in operations. And to
 * to enrich it with some useful information depending the use case.
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

Vue.component("detail-location-destination-operation", {
    mixins: [ItemDetailMixin],
    props: {
        color: String, // Used to determine card_color (See `utils.colors.color_for()`)
    },
    methods: {
        location_operation_detail_options() {
            return {
                main: false,
                title_icon: "mdi-package-variant-closed",
                fields: this.location_operation_detail_fields(),
                klass: "loud-labels",
            };
        },
        location_operation_detail_fields() {
            return [{path: "location_dest.name", label: "Location"}];
        },
    },
    template: `
     <div :class="$options._componentTag">

        <item-detail-card
            v-bind="$props"
            :card_color="utils.colors.color_for(color)"
            :key="make_component_key(['location-operation', record.id])"
            :options="location_operation_detail_options()"
            >
            <template v-slot:title>Destination</template>
        </item-detail-card>
    </div>
`,
});
