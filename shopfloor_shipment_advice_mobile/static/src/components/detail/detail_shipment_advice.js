/**
 * Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

Vue.component("detail-shipment", {
    mixins: [ItemDetailMixin],
    methods: {
        detail_fields() {
            return [
                {
                    path: "dock.name",
                    label: "Dock",
                },
                {path: "state", label: "Status"},
            ];
        },
        shipment_card_options() {
            return {
                main: true,
                fields: this.detail_fields(),
            };
        },
    },
    template: `
  <div :class="$options._componentTag">
    <item-detail-card
      v-bind="$props"
      :options="shipment_card_options()"
      :card_color="utils.colors.color_for('detail_main_card')">

      <template v-slot:title>
        {{ record.name }}
      </template>

    </item-detail-card>

  </div>
`,
});
