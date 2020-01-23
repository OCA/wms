export class Config {
  constructor() {
    this.apikey = localStorage.getItem('apikey');
    this.data = {}
    this.load()
  }

  get(key) {
    return this.data[key]
  }

  reset(apikey) {
    this.apikey=apikey;
    localStorage.setItem("apikey", apikey);
    this.load();
  }

  load() {
      // call odoo
      this.data = {
          'menu': [
              {name: 'Putaway', id: 1, scenario: 'single_pack_putaway'},
              {name: 'Transfer', id: 2, scenario: 'single_pack_transfer'},
          ],
          'profile': [
              {name: 'Test'},
              {name: 'Test'},
          ]
      }
      for (var idx in this.data['menu']) {
          var menu = this.data['menu'][idx]
          menu['hash'] = menu['scenario'] + menu['id']
      }
  }
}


