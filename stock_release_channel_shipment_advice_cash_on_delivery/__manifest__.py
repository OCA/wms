# Copyright 2018 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Release Channel Shipment Advice Cash on Delivery",
    "summary": """This module allows users to print cash on delivery invoices
    from a release channel and a shipment advice""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "BCIM, ACSONE SA/NV, Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "shipment_advice_cash_on_delivery",
        "stock_release_channel_shipment_advice",
    ],
    "data": [
        "views/stock_release_channel.xml",
    ],
}
