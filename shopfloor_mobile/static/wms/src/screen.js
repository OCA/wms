/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

//  Override main menu template

Vue.component("nav-item-content").extendOptions.template = `
    <div :class="$options._componentTag">
        <v-list-item-title class="primary--text">
            {{ item.name }}
        </v-list-item-title>
        <v-list-item-subtitle v-if="show_full_info">
            <small class="font-weight-light"><strong>{{ $t('app.nav.scenario') }}</strong> {{ item.scenario }}</small>
            <div v-if="!_.isEmpty(item.picking_types)">
                <small class="font-weight-light text-wrap pr-2">
                    <strong>{{ $t('app.nav.op_types') }}</strong>
                    <span v-for="(pt, index) in item.picking_types"
                            :key="'pt-' + item.id + '-' + pt.id"
                            >{{ pt.name }}<span v-if="index != (item.picking_types.length - 1)">,</span>
                    </span>
                </small>
            </div>
        </v-list-item-subtitle>
    </div>
`;

Vue.component("nav-item-action").extendOptions.template = `
    <div :class="$options._componentTag">
        <div class="pa-4 secondary text-no-wrap rounded-pill" v-if="item.lines_count">
            {{ $t('misc.lines_count', item) }}
        </div>
    </div>
`;
