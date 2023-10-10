# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class IrCron(models.Model):
    _inherit = "ir.cron"

    warehouse_ids = fields.One2many("stock.warehouse", "sync_cron_id")
