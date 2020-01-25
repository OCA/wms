Vue.component('Screen', {
    template: `
    <v-app>
        <v-content>
            <v-container>
                <div class="screen">
                    <div class="wrapper">
                        <slot>Screen content</slot>
                    </div>
                </div>
            </v-container>
        </v-content>
    </v-app>
    `,
})
