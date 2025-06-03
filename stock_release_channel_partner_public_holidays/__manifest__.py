# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Partner Public Holidays",
    "summary": """
        Add an option to exclude the public holidays when assigning th release channel""",
    "version": "16.0.2.1.0",
    "license": "AGPL-3",
    "maintainers": ["jbaudoux"],
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "hr_holidays_public",
        "stock_release_channel_shipment_lead_time",
    ],
    "data": [
        "views/stock_release_channel.xml",
    ],
}
