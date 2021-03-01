/**
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/**
 * Stored configuration object.
 *
 * Holds configuration for properties that can be stored on local storage
 * and Vue component data.
 */
class StoredConfig {
    constructor(registry, key, meta = {}) {
        _.defaults(meta, {
            default: "",
            reset_on_clear: false,
        });
        this.registry = registry;
        this.key = key;
        this.default = meta.default;
        this.reset_on_clear = meta.reset_on_clear;
    }
    _safe_value(v) {
        return v == null ? this.default : v;
    }
}

/**
 * Configuration registry.
 *
 * Configurations are computed properties that are stored into local storage too.
 * You can add your own configurations to the main app.
 * Each new key will be added to root computed properties.
 * They will be: reactive and at the same time stored in local storage
 * to support refreshing screens or resuming processes.
 *
 * To use it, simply import the registry and run
 *
 *     config_registry.add("profile", {default: {}, reset_on_clear: true})
 */
export class ConfigRegistry {
    constructor() {
        this._config = {};
        this.root = null;
        this.to_reset_on_clear = [];
        this._current_value_prefix = "current_";
    }
    /**
     * Set Vue root object.
     *
     * @param {*} root: reference to the current Vue app root.
     */
    _set_root(root) {
        this.root = root;
    }
    /**
     * Add a new configuration key.
     *
     * @param {*} key: the unique key
     * @param {*} meta: metadata to customize behavior.
     */
    add(key, meta) {
        const config = new StoredConfig(this, key, meta);
        this._config[key] = config;
        if (config.reset_on_clear) {
            this.to_reset_on_clear.push(config.key);
        }
    }
    /**
     * Return all configurations.
     */
    all() {
        return this._config;
    }
    /**
     * Return specific configuration via unique key
     *
     * @param {*} key
     */
    get(key) {
        return this._config[key];
    }
    /**
     * Flush all stored properties during an app clear config.
     */
    reset_on_clear() {
        const self = this;
        this.to_reset_on_clear.forEach(function(key) {
            self.reset(key);
        });
    }
    _get_root_val(k) {
        return this.root[this._current_value_prefix + k];
    }
    _set_root_val(k, v) {
        this.root[this._current_value_prefix + k] = v;
    }
    _get_storage_val(k) {
        return this.root.$storage.get(k);
    }
    _set_storage_val(k, v) {
        this.root.$storage.set(k, v);
    }
    /**
     * Retrieve the value of given config key.
     *
     * Lookup order:
     * 1. root value (fresh Vue component data)
     * 2. fallback to storage value
     * 3. fallback to default value if none of the above works
     *
     * @param {*} k: the key of the config
     */
    get_value(k) {
        const config = this.get(k);
        let val = this._get_root_val(config.key);
        if (_.isEmpty(val)) {
            val = this._get_storage_val(config.key);
        }
        if (_.isEmpty(val)) {
            val = config._safe_value(val);
        }
        return val;
    }
    /**
     * Store value for given config key.
     *
     * Store it both on the root component and in the local storage.
     * @param {*} k
     * @param {*} v
     */
    set_value(k, v) {
        // TODO: merge values for objects
        // const config = this.get(k);
        // let val = config._safe_value(v);
        // const new_data = _.merge({}, this.root[this.data_key], {[this.key]: v});
        this._set_root_val(k, v);
        this._set_storage_val(k, v);
    }
    /**
     * Reset given config key to default value.
     *
     * @param {*} k
     */
    reset(k) {
        const config = this.get(k);
        this._set_root_val(k, config.default);
        this.root.$storage.remove(k);
    }
    /**
     * Generate mapping suitable for components' computed properties.
     *
     * Getter and setter are provided for each registerd config.
     */
    generate_computed_properties() {
        const self = this;
        let result = {};
        _.each(this.all(), function(config) {
            result[config.key] = self._make_computed_prop(config.key);
        });
        return result;
    }
    /**
     * Generate mapping suitable for components' data.
     *
     * The value of each property is store on the component as
     *
     *  _current_value_prefix + config key
     */
    generare_data_keys() {
        const self = this;
        let data = {};
        _.each(self.all(), function(config) {
            data[self._current_value_prefix + config.key] = config.default || null;
        });
        return data;
    }
    /**
     * Generate single computed property mapping.
     * @param {*} key
     */
    _make_computed_prop(key) {
        return {
            get: _.partial(this.get_value.bind(this), key),
            set: _.partial(this.set_value.bind(this), key),
        };
    }
}

export var config_registry = new ConfigRegistry();
