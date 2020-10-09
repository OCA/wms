# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from datetime import datetime, timedelta

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ShopfloorLog(models.Model):
    _name = "shopfloor.log"
    _description = "Shopfloor Logging"
    _order = "id desc"

    DEFAULT_RETENTION = 30  # days

    request_url = fields.Char(readonly=True, string="Request URL")
    request_method = fields.Char(readonly=True)
    params = fields.Text(readonly=True)
    headers = fields.Text(readonly=True)
    result = fields.Text(readonly=True)
    error = fields.Text(readonly=True)
    state = fields.Selection(
        selection=[("success", "Success"), ("failed", "Failed")], readonly=True,
    )

    def _logs_retention_days(self):
        retention = self.DEFAULT_RETENTION
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("shopfloor.log.retention.days")
        )
        if param:
            try:
                retention = int(param)
            except ValueError:
                _logger.exception(
                    "Could not convert System Parameter"
                    " 'shopfloor.log.retention.days' to integer,"
                    " reverting to the"
                    " default configuration."
                )
        return retention

    def logging_active(self):
        retention = self._logs_retention_days()
        return retention > 0

    def autovacuum(self):
        """Delete logs which have exceeded their retention duration

        Called from a cron.
        """
        deadline = datetime.now() - timedelta(days=self._logs_retention_days())
        logs = self.search([("create_date", "<=", deadline)])
        if logs:
            logs.unlink()
        return True
