# Copyright 2020 Camptocamp
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import Command

from odoo.addons.component.core import Component
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

_logger = logging.getLogger(__name__)
# Inspired by https://github.com/OCA/wms/pull/119
PRIORITY_NORMAL = PROCUREMENT_PRIORITIES[0][0]


class PickingBatchAutoCreateAction(Component):
    """Automatic creation of picking batches"""

    _name = "shopfloor.picking.batch.auto.create"
    _inherit = "shopfloor.process.action"
    _usage = "picking.batch.auto.create"

    _advisory_lock_name = "shopfloor_batch_picking_create"

    def create_batch(
        self,
        picking_types,
        group_by_commercial_partner=False,
        maximum_number_of_preparation_lines=False,
        stock_device_types=None,
        **kwargs
    ):
        make_picking_batch = self.env["make.picking.batch"].create(
            self._prepare_make_picking_batch_values(
                picking_types,
                group_by_commercial_partner=group_by_commercial_partner,
                maximum_number_of_preparation_lines=maximum_number_of_preparation_lines,
                stock_device_types=stock_device_types,
                **kwargs
            )
        )
        return make_picking_batch._create_batch(raise_if_not_possible=False)

    def _prepare_make_picking_batch_values(
        self,
        picking_types,
        group_by_commercial_partner=False,
        maximum_number_of_preparation_lines=False,
        stock_device_types=None,
        **kwargs
    ):
        values = {
            "restrict_to_same_partner": group_by_commercial_partner,
            "maximum_number_of_preparation_lines": maximum_number_of_preparation_lines,
            "restrict_to_same_priority": True,
        }
        if picking_types and picking_types.ids:
            values["picking_type_ids"] = [Command.set(picking_types.ids)]

        if stock_device_types and stock_device_types.ids:
            values["stock_device_type_ids"] = [Command.set(stock_device_types.ids)]
        return values
