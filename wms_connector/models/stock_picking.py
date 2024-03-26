# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = ["synchronize.exportable.mixin", "stock.picking"]
    _name = "stock.picking"

    is_wms_exportable = fields.Boolean(
        compute="_compute_is_wms_exportable", readonly=True, store=True
    )
    wms_sync_cancel_supported = fields.Boolean(
        compute="_compute_wms_sync_cancel_supported"
    )
    wms_import_attachment_id = fields.Many2one(
        "attachment.queue", index=True, readonly=True
    )
    wms_export_date = fields.Datetime(tracking=True)

    def _get_wms_export_task(self):
        return self.picking_type_id.warehouse_id.sudo().wms_export_task_id

    def _compute_wms_sync_cancel_supported(self):
        self.wms_sync_cancel_supported = False

    @api.depends(
        "picking_type_id.warehouse_id.active_wms_sync",
        "picking_type_id.code",
    )
    def _compute_is_wms_exportable(self):
        for rec in self:
            rec.is_wms_exportable = (
                rec.picking_type_id.warehouse_id.active_wms_sync
                and rec.picking_type_id.code in ("incoming", "outgoing")
            )

    def _is_user_allowed_to_cancel(self):
        return self.env.user.has_group("stock.group_stock_manager")

    def action_force_cancel_wms(self):
        if not self._is_user_allowed_to_cancel():
            raise UserError(_("You are not allowed to cancel this picking"))
        self.wms_export_date = None
        self.wms_export_attachment_id = None
        return self.with_context(skip_wms_cancel_check=True).action_cancel()

    def action_cancel(self):
        for record in self.filtered(lambda p: p.state != "cancel"):
            if (
                not self._context.get("skip_wms_cancel_check")
                and record.wms_export_date
                and not record.wms_sync_cancel_supported
            ):
                raise UserError(
                    _(
                        "The picking %s can not be deleted as it have been sent "
                        "to the WMS, ask your manager to force the cancellation"
                    )
                    % record.name
                )
        return super().action_cancel()

    def _wms_check_if_editable(self):
        if self._context.get("skip_check_protected_fields"):
            return True
        for picking in self:
            if picking.wms_export_date:
                raise UserError(
                    _("The picking %s have been exported and can not be modified")
                    % picking.name
                )
