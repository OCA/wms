var homepage = Vue.component('home-page', {
    computed: {
        navigation () {
            return this.$root.config.get('menu');
            }
        },
    props:['routes'],
    template: `
    <div>
        <a v-for="nav in this.navigation" v-bind:href="'#' + nav.hash" class="btn btn-primary btn-lg btn-block">{{ nav.name }}</a>
        <p v-if="this.$root.using_demo_url" class="text-center">Using demo url</p>
    </div>

    `
});
