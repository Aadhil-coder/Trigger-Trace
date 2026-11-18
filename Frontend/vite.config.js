import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: false, // the manifest is public/manifest.json
      includeAssets: ["icons/apple-touch-icon.png"],
      workbox: {
        globPatterns: ["**/*.{js,css,html,png,svg}"],
        navigateFallback: "/index.html",
        runtimeCaching: [
          {
            // Try the backend first, fall back to the last saved response when offline
            urlPattern: /\/api\/.*/i,
            handler: "NetworkFirst",
            options: { cacheName: "api", networkTimeoutSeconds: 5 },
          },
        ],
      },
    }),
  ],
  server: {
    host: true,   // lets your phone reach the dev server on the same Wi-Fi
    port: 5173,
    proxy: {
      // Requests to /api go to the Flask backend, so no CORS setup is needed
      "/api": "http://localhost:8000",
    },
  },
});
