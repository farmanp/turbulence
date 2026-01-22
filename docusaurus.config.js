// @ts-check

const { themes } = require("prism-react-renderer");
const lightCodeTheme = themes.github;
const darkCodeTheme = themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "Windtunnel",
  tagline: "High-performance workflow simulation and testing framework",
  url: "http://localhost",
  baseUrl: "/",
  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",
  favicon: "img/windtunnel-logo.svg",

  organizationName: "windtunnel",
  projectName: "windtunnel",

  presets: [
    [
      "@docusaurus/preset-classic",
      {
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
          routeBasePath: "/"
        },
        blog: false,
        theme: {
          customCss: require.resolve("./src/css/custom.css")
        }
      }
    ]
  ],

  themeConfig: {
    navbar: {
      title: "Windtunnel",
      logo: {
        alt: "Windtunnel",
        src: "img/windtunnel-logo.svg"
      },
      items: [
        {
          type: "doc",
          docId: "intro",
          position: "left",
          label: "Docs"
        }
      ]
    },
    prism: {
      theme: lightCodeTheme,
      darkTheme: darkCodeTheme
    }
  }
};

module.exports = config;
