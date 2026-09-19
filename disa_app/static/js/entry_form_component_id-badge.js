
// A DISA form ID badge

const template = `
  <span class="badge rounded-pill bg-secondary text-light disa-id-badge"
        vv-on:click="optionsMenu()"
        data-bs-toggle="popover"
        data-bs-animation="false"
        title="Click for sharing options">
    ID:{{ displayId(forthis.id || forthis.uuid) }}
  </span>
`;

const componentDefinition = {
  props: ['forthis'],
  template,
  methods: {
    displayId: function (longId) {
      return longId.toString().slice(0,5);
    },
    optionsMenu: function(x, e) {
      //console.log('options!', x, e);
    }
  },
  mounted: function () {
    const tooltip =  new bootstrap.Tooltip(this.$el);
    tooltip.html = true;
    tooltip.title = "YES and <em>yes</em>!";
  }
};

export { componentDefinition as DISA_ID_COMPONENT }
