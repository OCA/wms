# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.tools import sql

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    sql.rename_column(cr, "stock_release_channel", "auto_release", "batch_mode")
    sql.rename_column(cr, "stock_release_channel", "max_auto_release", "max_batch_mode")
