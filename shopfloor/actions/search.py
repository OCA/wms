from odoo.addons.component.core import Component


class SearchAction(Component):
    """Provide methods to search records from scanner

    The methods should be used in Service Components, so a search will always
    have the same result in all scenarios.
    """

    _name = "shopfloor.search.action"
    _inherit = "shopfloor.process.action"
    _usage = "search"

    def location_from_scan(self, barcode):
        return self.env["stock.location"].search([("barcode", "=", barcode)])

    def package_from_scan(self, barcode):
        return self.env["stock.quant.package"].search([("name", "=", barcode)])
