Vue.component('ScreenHeader', {
  data: () => {
    return {}
  },
  props:['screen_title'],
  template: `
  <div class="screen-header">
    <a href="#" class="btn btn-lg btn-outline-secondary app-nav app-nav-home"><span>Back</span></a>
    <div class="screen-title h1">{{ screen_title }}</div>
  </div>
`
})
