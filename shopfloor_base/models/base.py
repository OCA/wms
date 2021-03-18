# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import models


class Base(models.AbstractModel):

    _inherit = "base"

    def jsonify(self, parser, one=False):
        # Add support for params one... provided by base_jsonify from 13.0
        if one:
            self.ensure_one()
        result = super(Base, self).jsonify(parser)
        return result[0] if one else result
