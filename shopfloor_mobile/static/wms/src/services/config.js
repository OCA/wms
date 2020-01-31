import {Odoo} from './odoo.js'
import {Storage} from './storage.js'

export class Config {
  constructor() {
    this.data = {}
    this.authenticated = false
  }

  get(key) {
    return this.data[key]
  }

  load() {
      var odoo = new Odoo({usage: "app"})
      return odoo._call('user_config', 'POST', {})
          .then((data) => {
              this.data = data['data'];
              for (var idx in this.data['menus']) {
                  var menu = this.data['menus'][idx]
                  menu['hash'] = menu['process'] + '_' + menu['id']
              };
              this.authenticated = true
          });
  }
}
