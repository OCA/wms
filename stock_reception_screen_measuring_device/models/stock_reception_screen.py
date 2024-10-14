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
    smaller_package_has_missing_dimensions = fields.Boolean(
        "Smaller Package Requires Measures?",
        compute="_compute_smaller_package_has_missing_dimensions",
        store=True,
        help="Indicates if any smaller package have any measurement missing.",
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

    @api.depends(
        "current_move_product_id.packaging_ids.measuring_device_id",
    )
    def _compute_scan_requested(self):
        for record in self:
            # TODO
            all_product_packagings = record.current_move_product_id.packaging_ids
            record.scan_requested = False
            for packaging in all_product_packagings:
                if packaging.measuring_device_id:
                    record.scan_requested = True
                    break

    @api.depends(
        "product_packaging_id.packaging_length",
        "product_packaging_id.width",
        "product_packaging_id.height",
    )
    def _compute_package_dimensions(self):
        for record in self:
            pack = record.product_packaging_id
            dimension_values = [pack.packaging_length, pack.height, pack.width]
            if all(dimension_values):
                record.display_package_dimensions = " x ".join(
                    [f"{str(val)}mm" for val in dimension_values]
                )
            else:
                record.display_package_dimensions = False

    @api.depends(
        "product_packaging_id",
        "product_packaging_id.qty",
        "current_move_product_id.packaging_ids.max_weight",
        "current_move_product_id.packaging_ids.packaging_length",
        "current_move_product_id.packaging_ids.width",
        "current_move_product_id.packaging_ids.height",
    )
    def _compute_smaller_package_has_missing_dimensions(self):
        for record in self:
            record.smaller_package_has_missing_dimensions = bool(
                record._get_smaller_package_without_dimensions()
            )

    @api.depends(
        "product_packaging_id.max_weight",
        "product_packaging_id.packaging_length",
        "product_packaging_id.width",
        "product_packaging_id.height",
    )
    def _compute_package_has_missing_dimensions(self):
        for record in self:
            pack = record.product_packaging_id
            if pack:
                record.package_has_missing_dimensions = not pack.type_is_pallet and (
                    not (pack.packaging_length and pack.width and pack.height)
                    or not pack.max_weight
                )
            else:
                record.package_has_missing_dimensions = False

    @api.model
    def _measure_packaging(self, packaging):
        device = self.env["measuring.device"].search(
            [("is_default", "=", True)], limit=1
        )
        if not device:
            error_msg = _("No default device set, please configure one.")
            _logger.error(error_msg)
            self._notify(error_msg)
            raise UserError(error_msg)
        if device._is_being_used():
            error_msg = _("Measurement machine already in use.")
            _logger.error(error_msg)
            self._notify(error_msg)
            raise UserError(error_msg)

        packaging._measuring_device_assign(device)
        return True

    def measure_current_packaging(self):
        self.ensure_one()
        return self._measure_packaging(self.product_packaging_id)

    def _get_smaller_package_without_dimensions_domain(self):
        self.ensure_one()
        # TODO ordered package
        return [
            ("product_id", "=", self.current_move_product_id.id),
            ("qty", "<", self.product_packaging_id.qty),
            "|",
            "|",
            "|",
            ("packaging_length", "=", False),
            ("width", "=", False),
            ("height", "=", False),
            ("max_weight", "=", False),
        ]

    def _get_smaller_package_without_dimensions(self):
        self.ensure_one()
        domain = self._get_smaller_package_without_dimensions_domain()
        return self.env["product.packaging"].search(domain, order="qty desc", limit=1)

    def measure_smaller_packaging(self):
        self.ensure_one()
        pack_without_dimensions = self._get_smaller_package_without_dimensions()
        if not pack_without_dimensions:
            error_msg = _("No available packaging without measurements.")
            raise UserError(error_msg)
        return self._measure_packaging(pack_without_dimensions)

    def cancel_measure_current_packaging(self):
        self.ensure_one()
        assigned_packaging = self.current_move_product_id.packaging_ids.filtered(
            lambda p: p.measuring_device_id
        )
        assigned_packaging._measuring_device_release()

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
