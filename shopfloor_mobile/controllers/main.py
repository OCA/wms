import os

from odoo import http


class ShopfloorMobileAppController(http.Controller):

    module_path = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]

    @http.route('/shopfloormobile/scanner/', auth='public')
    def load_mobile_app(self):
        index_file = os.path.join(self.module_path, 'static', 'wms', 'index.html')
        return http.send_file(index_file)

    @http.route('/shopfloormobile/scanner/<path:path_fragment>', auth='public')
    def load_app_assets(self, path_fragment=''):
        index_file = os.path.join(self.module_path, 'static', 'wms', path_fragment)
        return http.send_file(index_file)
