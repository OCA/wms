/**
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
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
        if (!_.isEmpty(meta.storage)) {
            const is_driver_allowed = this._is_storage_driver_allowed(
                meta.storage.driver
            );
            if (!is_driver_allowed) {
                throw new Error(
                    "Storage driver not allowed. Allowed types: 'local', 'session', 'memory'"
                );
            }
        }
        this.storage = meta.storage || {};
    }
    _safe_value(v) {
        return v === null ? this.default : v;
    }
    _is_storage_driver_allowed(driver) {
        // TODO: these permitted types are hardcoded, matching the driver types of Vue2Storage.
        // If possible, we should be able to get them from the library class instead.
        return ["local", "session", "memory"].includes(driver);
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
        this.storage_defaults = {};
    }
    /**
     * Set Vue root object.
     *
     * @param {*} root: reference to the current Vue app root.
     */
    setup(root) {
        this.root = root;
        this._set_storage_defaults();
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
        this.to_reset_on_clear.forEach(function (key) {
            self.reset(key);
        });
    }
    _set_storage_defaults() {
        this.storage_defaults = this.root.$storage.options;
    }
    _get_root_val(config) {
        return this.root[this._current_value_prefix + config.key];
    }
    _set_root_val(config, v) {
        this.root[this._current_value_prefix + config.key] = v;
    }
    _get_storage_val(config) {
        if (config.storage.driver) {
            this._switch_storage_driver(config.storage);
        }
        const value = this.root.$storage.get(config.key);
        if (config.storage.driver) {
            this._reset_storage_driver();
        }
        return value;
    }
    _set_storage_val(config, v) {
        if (config.storage.driver) {
            this._switch_storage_driver(config.storage);
        }
        this.root.$storage.set(config.key, v);
        if (config.storage.driver) {
            this._reset_storage_driver();
        }
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
        let val = this._get_root_val(config);
        if (_.isEmpty(val)) {
            val = this._get_storage_val(config);
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
        const config = this.get(k);
        this._set_root_val(config, v);
        this._set_storage_val(config, v);
    }

    _switch_storage_driver(storage) {
        // The app uses sessionStorage by default (currently set on app creation).
        // If any piece of data needs to be handled by localStorage,
        // we switch the vue2storage driver option to "local", we store / retrieve the value,
        // and then we revert to "session" for further use.
        // See example in documentation: https://github.com/yarkovaleksei/vue2-storage/blob/master/docs/en/started.md
        this.root.$storage.setOptions({
            prefix: storage.prefix || this.storage_defaults.prefix,
            driver: storage.driver || this.storage_defaults.driver,
            ttl: storage.ttl || this.storage_defaults.ttl,
        });
    }

    _reset_storage_driver() {
        this.root.$storage.setOptions({
            prefix: this.storage_defaults.prefix,
            driver: this.storage_defaults.driver,
            ttl: this.storage_defaults.ttl,
        });
    }
    /**
     * Reset given config key to default value.
     *
     * @param {*} k
     */
    reset(k) {
        const config = this.get(k);
        this._set_root_val(config, config.default);
        this.root.$storage.remove(config.key);
    }
    /**
     * Generate mapping suitable for components' computed properties.
     *
     * Getter and setter are provided for each registerd config.
     */
    generate_computed_properties() {
        const self = this;
        const result = {};
        _.each(this.all(), function (config) {
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
        const data = {};
        _.each(self.all(), function (config) {
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
