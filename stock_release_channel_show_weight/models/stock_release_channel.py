# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    weight_uom_name = fields.Char(
        string="Weight Unit of Measure label", compute="_compute_weight_uom_name"
    )

    def _compute_weight_uom_name(self):
        self.weight_uom_name = self.env[
            "product.template"
        ]._get_weight_uom_name_from_ir_config_parameter()

    weight_picking_all = fields.Float(
        string="All Transfers Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_picking_release_ready = fields.Float(
        string="Release Ready Transfers Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_picking_released = fields.Float(
        string="Released Transfers Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_picking_assigned = fields.Float(
        string="Available Transfers Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_picking_waiting = fields.Float(
        string="Waiting Transfers Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_picking_late = fields.Float(
        string="Late Transfers Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_picking_priority = fields.Float(
        string="Priority Transfers Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_picking_done = fields.Float(
        string="Transfers Done  WeightToday",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_picking_full_progress = fields.Float(
        string="Full Progress Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_move_all = fields.Float(
        string="All Moves (Estimate) Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_move_release_ready = fields.Float(
        string="Release Ready Moves (Estimate) Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_move_released = fields.Float(
        string="Released Moves (Estimate) Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_move_assigned = fields.Float(
        string="Available Moves (Estimate) Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_move_waiting = fields.Float(
        string="Waiting Moves (Estimate) Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_move_late = fields.Float(
        string="Late Moves (Estimate) Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_move_priority = fields.Float(
        string="Priority Moves (Estimate) Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )
    weight_move_done = fields.Float(
        string="Moves Done Today (Estimate) Weight",
        compute="_compute_picking_count",
        digits="Release Channel Weight",
    )

    @api.model
    def _get_picking_read_group_fields(self):
        res = super()._get_picking_read_group_fields()
        res += ["weight"]
        return res

    @api.model
    def _get_move_read_group_fields(self):
        res = super()._get_move_read_group_fields()
        res += ["weight"]
        return res

    @api.model
    def _get_picking_compute_fields(self):
        res = super()._get_picking_compute_fields()
        res += [("weight", "weight")]
        return res

    @api.model
    def _get_move_compute_fields(self):
        res = super()._get_move_compute_fields()
        res += [("weight", "weight")]
        return res
