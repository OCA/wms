import {Odoo} from "./odoo.js";

export class Config {
    constructor() {
        this.data = {};
        this.authenticated = false;
    }

    get(key) {
        return this.data[key];
    }

    load() {
        var odoo = new Odoo({usage: "app"});
        return odoo._call("app/user_config", "POST", {}).then(result => {
            if (!_.isUndefined(result.data)) {
                this.data = result.data;
                // TMP DEV add menu item for XXX process to draft
                this.authenticated = true;
            } else {
                console.log(result);
            }
            this.data.menus.push({
                id: 99,
                name: "Checkout",
                process: {id: 99, code: "checkout"},
            });
        });
    }
}
