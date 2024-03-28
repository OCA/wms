# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Propagate Channel Picking",
    "summary": """
        Allows to propagate the channel to every picking that is created from
        the original one.""",
    "version": "16.0.1.2.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": ["stock_release_channel"],
    "data": ["views/stock_picking_type.xml"],
}
