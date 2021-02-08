# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=odoo-addons-relative-import
from odoo.addons.stock_storage_type.hooks import add_pack_operation_state_column


def migrate(cr, version):
    if not version:
        return
    add_pack_operation_state_column(cr)
