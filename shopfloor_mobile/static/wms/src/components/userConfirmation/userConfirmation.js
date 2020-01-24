var userConfirmation = Vue.component('user-confirmation', {
  props: ['title', 'question'],
  methods: {},
  template: `

    <div class="confirm">
        <div class="alert alert-warning" role="alert">
            <h4 class="alert-heading">{{ this.title }}</h4>
            <p>{{ question }}</p>
            <form>
               <input v-on:click="$emit('user-confirmation', 'yes')" class="btn btn-lg btn-success" type="submit" value="Yes"></input>
               <input v-on:click="$emit('user-confirmation', 'no')" class="btn btn-lg btn-danger float-right" type="reset" value="No"></input>
            </form>
        </div>
    </div>

`,
})
