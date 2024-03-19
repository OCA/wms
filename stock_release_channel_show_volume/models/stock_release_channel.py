# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    volume_uom_name = fields.Char(
        string="Volume Unit of Measure label", compute="_compute_volume_uom_name"
    )

    def _compute_volume_uom_name(self):
        self.volume_uom_name = self.env[
            "product.template"
        ]._get_volume_uom_name_from_ir_config_parameter()

    volume_picking_all = fields.Float(
        string="All Transfers Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_picking_release_ready = fields.Float(
        string="Release Ready Transfers Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_picking_released = fields.Float(
        string="Released Transfers Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_picking_assigned = fields.Float(
        string="Available Transfers Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_picking_waiting = fields.Float(
        string="Waiting Transfers Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_picking_late = fields.Float(
        string="Late Transfers Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_picking_priority = fields.Float(
        string="Priority Transfers Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_picking_done = fields.Float(
        string="Transfers Done  VolumeToday",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_picking_full_progress = fields.Float(
        string="Full Progress Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_move_all = fields.Float(
        string="All Moves (Estimate) Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_move_release_ready = fields.Float(
        string="Release Ready Moves (Estimate) Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_move_released = fields.Float(
        string="Released Moves (Estimate) Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_move_assigned = fields.Float(
        string="Available Moves (Estimate) Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_move_waiting = fields.Float(
        string="Waiting Moves (Estimate) Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_move_late = fields.Float(
        string="Late Moves (Estimate) Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_move_priority = fields.Float(
        string="Priority Moves (Estimate) Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )
    volume_move_done = fields.Float(
        string="Moves Done Today (Estimate) Volume",
        compute="_compute_picking_count",
        digits="Release Channel Volume",
    )

    @api.model
    def _get_picking_read_group_fields(self):
        res = super()._get_picking_read_group_fields()
        res += ["volume"]
        return res

    @api.model
    def _get_move_read_group_fields(self):
        res = super()._get_move_read_group_fields()
        res += ["volume"]
        return res

    @api.model
    def _get_picking_compute_fields(self):
        res = super()._get_picking_compute_fields()
        res += [("volume", "volume")]
        return res

    @api.model
    def _get_move_compute_fields(self):
        res = super()._get_move_compute_fields()
        res += [("volume", "volume")]
        return res
