export default {
  base: "./",
  build: {
    lib: {
      entry: "./src/main.js",
      name: "openmeshedanatomy",
      formats: ["umd"],
      fileName: "openmeshedanatomy",
    },
    rollupOptions: {
      external: ["vue"],
      output: {
        globals: {
          vue: "Vue",
        },
      },
    },
    outDir: "../src/openmeshedanatomy/module/serve",
    assetsDir: ".",
  },
};
