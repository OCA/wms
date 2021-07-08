/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Francois Poizat <francois.poizat@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/wms/src/components/detail/detail_mixin.js";

Vue.component("detail-simple-picking", {
    mixins: [ItemDetailMixin],
    props: ["options"],
    template: `
  <div :class="$options._componentTag" v-on="$listeners">
    <item-detail-card
      v-bind="$props"
      :options="options"
      :card_color="utils.colors.color_for('detail_main_card')">
      <template v-slot:subtitle>
        {{ record.complete_name }}
      </template>
    </item-detail-card>
  </div>
`,
});
