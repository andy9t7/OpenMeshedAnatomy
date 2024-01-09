export default {
  base: "./",
  build: {
    lib: {
      entry: "./src/main.js",
      name: "oma",
      formats: ["umd"],
      fileName: "oma",
    },
    rollupOptions: {
      external: ["vue"],
      output: {
        globals: {
          vue: "Vue",
        },
      },
    },
    outDir: "../oma/module/serve",
    assetsDir: ".",
  },
};
