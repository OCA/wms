# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.component.core import Component


class DataDetailAction(Component):
    """Provide extra data on top of data action.
    """

    _name = "shopfloor.data.detail.action"
    _inherit = "shopfloor.data.action"
    _usage = "data_detail"
