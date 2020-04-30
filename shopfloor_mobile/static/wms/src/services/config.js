export class Config {
    constructor(odoo) {
        this.odoo = odoo;
        this.data = {};
        this.authenticated = false;
    }
    load() {
        return this.odoo._call("app/user_config", "POST", {}).then(result => {
            if (!_.isUndefined(result.data)) {
                this.data = result.data;
                this.authenticated = true;
            } else {
                // TODO: any better thing to do here?
                console.log(result);
            }
        });
    }
}
