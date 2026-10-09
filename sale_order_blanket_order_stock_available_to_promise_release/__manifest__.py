# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Order Blanket Order Stock Available to Promise Release",
    "summary": "Display and filter ATP release availability for blanket call-offs",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "sale_order_blanket_order_stock_prebook_release",
        "sale_stock_prebook_stock_available_to_promise_release",
        "sale_stock_available_to_promise_release",
    ],
    "data": [
        "wizards/sale_order_deliver_remaining_wizard.xml",
    ],
    "auto_install": True,
    "installable": True,
}
