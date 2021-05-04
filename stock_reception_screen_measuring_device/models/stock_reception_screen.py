# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockReceptionScreen(models.Model):
    _inherit = "stock.reception.screen"

    package_has_missing_dimensions = fields.Boolean(
        "Package Requires Measures?",
        compute="_compute_package_has_missing_dimensions",
        store=True,
        help="Indicates if the package have any measurement missing.",
    )
    display_package_dimensions = fields.Char(
        string="Dimensions (lxhxw)",
        compute="_compute_package_dimensions",
        help="Dimensions of the package in mm (length x height x width)",
    )
    scan_requested = fields.Boolean(
        help="A scan from the measuring device was requested",
        default=False,
        compute="_compute_scan_requested",
        store=True,
    )

    @api.depends("product_packaging_id", "product_packaging_id.measuring_device_id")
    def _compute_scan_requested(self):
        for record in self:
            record.scan_requested = (
                record.product_packaging_id
                and record.product_packaging_id.measuring_device_id
            )

    @api.depends(
        "product_packaging_id.lngth",
        "product_packaging_id.width",
        "product_packaging_id.height",
    )
    def _compute_package_dimensions(self):
        for record in self:
            pack = record.product_packaging_id
            dimension_values = [pack.lngth, pack.height, pack.width]
            if all(dimension_values):
                record.display_package_dimensions = " x ".join(
                    [f"{str(val)}mm" for val in dimension_values]
                )
            else:
                record.display_package_dimensions = False

    @api.depends(
        "product_packaging_id.max_weight",
        "product_packaging_id.lngth",
        "product_packaging_id.width",
        "product_packaging_id.height",
    )
    def _compute_package_has_missing_dimensions(self):
        for record in self:
            pack = record.product_packaging_id
            if pack:
                record.package_has_missing_dimensions = not pack.type_is_pallet and (
                    not (pack.lngth and pack.width and pack.height)
                    or not pack.max_weight
                )
            else:
                record.package_has_missing_dimensions = False

    def measure_current_packaging(self):
        self.ensure_one()
        device = self.env["measuring.device"].search(
            [("is_default", "=", True)], limit=1
        )
        if not device:
            error_msg = _("No default device set, please configure one.")
            _logger.error(error_msg)
            self._notify(error_msg)
            return UserError(error_msg)
        if device._is_being_used():
            error_msg = _("Measurement machine already in use.")
            _logger.error(error_msg)
            self._notify(error_msg)
            return UserError(error_msg)

        self.product_packaging_id._measuring_device_assign(device)
        return True

    def cancel_measure_current_packaging(self):
        self.ensure_one()
        self.product_packaging_id._measuring_device_release()
        return True

    def _notify(self, message):
        """Show a gentle notification on the wizard"""
        self.ensure_one()
        self.create_uid.with_user(self.create_uid.id).notify_warning(message=message)

    def reload(self):
        self.cancel_measure_current_packaging()
        return {
            "type": "ir.actions.act_view_reload",
        }

    def button_reset(self):
        self.cancel_measure_current_packaging()
        return super().button_reset()
