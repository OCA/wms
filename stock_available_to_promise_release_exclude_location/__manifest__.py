# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Available To Promise Release Exclude Location",
    "summary": "Exclude locations from available stock",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, BCIM, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_available_to_promise_release",
        "stock_available_immediately_exclude_location",
    ],
    "installable": True,
    "auto_install": True,
    "application": False,
}
