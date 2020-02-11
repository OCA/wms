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
          .then((result) => {
            if (!_.isUndefined(result.data)) {
              this.data = result.data;
              this.authenticated = true
            } else {
              console.log(result)
            }
          });
  }
}
