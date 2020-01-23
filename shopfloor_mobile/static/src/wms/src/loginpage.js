var loginpage = Vue.component('login-page', {
    data: function(){ return {
        'username': '',
        'password': '',
        'accessbadge': '',
    }},
    methods: {
        login: function() {
            if ((this.username == this.password) || (accessbadge == '123') ) {
                this.$root.authenticated = true;
                // this.$root.currentRoute = '';
            } else {
                this.$root.authenticated = false;
                this.username = '';
                this.password = '';
            }
        }
    },
    template: `

    <form>
    <h1 class="text-center">WMS</h1>
  <div class="form-group">
    <input type="text" class="form-control" v-model="accessbadge" placeholder="Scan your access badge" autofocus>
  </div>
  <div class="form-group">
    <label class="text-muted">Or enter your credentials</label>
  </div>

  <div class="form-group">
    <input type="text" class="form-control" v-model="username" placeholder="Username">
  </div>
  <div class="form-group">
    <input type="password" class="form-control" v-model="password" placeholder="Password">
  </div>
  <button type="button" class="btn btn-primary btn-block" v-on:click="login()">Login</button>
</form>



    `
});

