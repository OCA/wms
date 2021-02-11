let VueSuperMethod = function (_options) {
    /**
     * Making a proxy super method for calling Super.
     * This will applicatible for mixin methods and extended component methods
     */
    
    // Creating a Proxy instance with options. This options will be our class/mixin/component name
    return new Proxy(_options, {
        get: (_options, name) => {
        // Checking if the given method is exist of method objects/list
        if (_options.methods && name in _options.methods) {
            // If YES? just call and return the data
            return _options.methods[name].bind(this)
        }
        }
    })
}


// this was: module.exports = VueSuperMethod -> fixed as:
export default VueSuperMethod
