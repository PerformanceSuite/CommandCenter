import { defineConfig, splitVendorChunkPlugin } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { visualizer } from 'rollup-plugin-visualizer'
import compression from 'vite-plugin-compression'

// Performance-optimized Vite configuration
export default defineConfig({
  plugins: [
    react(),
    splitVendorChunkPlugin(),
    // Generate bundle analysis (optional, remove for production)
    visualizer({
      filename: './dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    }),
    // Pre-compress assets for production
    compression({
      algorithm: 'gzip',
      ext: '.gz',
    }),
    compression({
      algorithm: 'brotliCompress',
      ext: '.br',
    }),
  ],

  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // WebSocket proxy for real-time updates
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@services': path.resolve(__dirname, './src/services'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
    },
  },

  build: {
    // Output directory
    outDir: 'dist',

    // Generate source maps for production debugging
    sourcemap: false, // Set to true for debugging production issues

    // Minification options
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,      // Remove console logs
        drop_debugger: true,     // Remove debugger statements
        pure_funcs: ['console.log', 'console.info'], // Remove specific functions
        passes: 2,               // Multiple compression passes
      },
      mangle: {
        safari10: true,          // Work around Safari 10 bugs
      },
      format: {
        comments: false,         // Remove comments
      },
    },

    // Chunk size warnings
    chunkSizeWarningLimit: 1000, // 1MB warning threshold

    // Rollup options for code splitting
    rollupOptions: {
      output: {
        // Manual chunks for better caching
        manualChunks: (id) => {
          // Core vendor libraries
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom')) {
              return 'react-vendor';
            }
            if (id.includes('react-router')) {
              return 'router';
            }
            if (id.includes('@tanstack/react-query')) {
              return 'query';
            }
            if (id.includes('chart.js') || id.includes('react-chartjs')) {
              return 'charts';
            }
            if (id.includes('axios')) {
              return 'http';
            }
            if (id.includes('lucide-react')) {
              return 'icons';
            }
            // All other vendor code
            return 'vendor';
          }

          // Application code splitting by feature
          if (id.includes('src/pages/Dashboard')) {
            return 'dashboard';
          }
          if (id.includes('src/pages/TechnologyRadar')) {
            return 'radar';
          }
          if (id.includes('src/pages/ResearchHub')) {
            return 'research';
          }
          if (id.includes('src/pages/KnowledgeBase')) {
            return 'knowledge';
          }
          if (id.includes('src/components/common')) {
            return 'common';
          }
        },

        // Asset naming for better caching
        assetFileNames: (assetInfo) => {
          if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(assetInfo.name)) {
            return `assets/images/[name]-[hash][extname]`;
          }
          if (/\.(woff2?|ttf|otf|eot)$/i.test(assetInfo.name)) {
            return `assets/fonts/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },

        // Chunk naming
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
      },
    },

    // CSS code splitting
    cssCodeSplit: true,

    // Asset size threshold for inlining (4KB)
    assetsInlineLimit: 4096,

    // Target modern browsers for smaller bundles
    target: 'es2020',

    // Report compressed size
    reportCompressedSize: false, // Disable for faster builds
  },

  // Optimize dependencies
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'axios',
      'chart.js',
    ],
    exclude: [],
    esbuildOptions: {
      target: 'es2020',
    },
  },

  // CSS configuration
  css: {
    modules: {
      localsConvention: 'camelCase',
    },
    preprocessorOptions: {
      css: {
        charset: false, // Avoid charset issues
      },
    },
  },

  // Preview server configuration
  preview: {
    port: 3000,
    strictPort: true,
    headers: {
      // Security headers
      'X-Frame-Options': 'SAMEORIGIN',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
      // Cache headers for static assets
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  },

  // Environment variable prefix
  envPrefix: 'VITE_',
})
