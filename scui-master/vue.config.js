const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
	publicPath: process.env.VUE_APP_PUBLIC_PATH,
	outputDir: 'dist',
	assetsDir: "static",
	productionSourceMap: false,
	devServer: {
		allowedHosts: 'all',
		open: false,
		port: process.env.VUE_APP_PORT || 2800,
		proxy: {
			'/api': {
				target: process.env.VUE_APP_API_BASEURL || 'http://127.0.0.1:5001',
				changeOrigin: true,
			}
		}
	},
	chainWebpack: config => {
		config.plugins.delete('preload');
		config.plugins.delete('prefetch');
		config.resolve.alias.set('vue-i18n', 'vue-i18n/dist/vue-i18n.cjs.js');
	},
	configureWebpack: {
		performance: {
			hints: false
		},
		optimization: {
			splitChunks: {
				chunks: "all",
				automaticNameDelimiter: '~',
				name: "scuiChunks",
				cacheGroups: {
					vendor: {
						name: "modules",
						test: /[\\/]node_modules[\\/]/,
						priority: -10
					},
					elicons: {
						name: "elicons",
						test: /[\\/]node_modules[\\/]@element-plus[\\/]icons-vue[\\/]/
					},
					tinymce: {
						name: "tinymce",
						test: /[\\/]node_modules[\\/]tinymce[\\/]/
					},
					echarts: {
						name: "echarts",
						test: /[\\/]node_modules[\\/]echarts[\\/]/
					},
					xgplayer: {
						name: "xgplayer",
						test: /[\\/]node_modules[\\/]xgplayer.*[\\/]/
					},
					codemirror: {
						name: "codemirror",
						test: /[\\/]node_modules[\\/]codemirror[\\/]/
					}
				}
			}
		}
	}
})
