/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    "intro",
    {
      type: "category",
      label: "User Guide",
      items: [
        "user/getting-started",
        "user/sut-config",
        "user/scenario-authoring",
        "user/templating",
        "user/cli",
        "user/reporting",
        "user/replay",
        "user/turbulence",
        "user/troubleshooting",
        {
          type: "category",
          label: "Guides",
          items: [
            "user/guides/ecommerce-testing"
          ]
        }
      ]
    },
    {
      type: "category",
      label: "Developer Guide",
      items: [
        "developer/development-setup",
        "developer/architecture",
        "developer/testing",
        "developer/contributing"
      ]
    },
    {
      type: "category",
      label: "Architecture & Research",
      items: [
        "architecture/decomposition",
        "architecture/dsl_research",
        "research/spikes/SPIKE-002-python-dsl"
      ]
    }
  ]
};

module.exports = sidebars;
