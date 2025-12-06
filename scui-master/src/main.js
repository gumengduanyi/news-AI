import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/display.css'
import scui from './scui'
import i18n from './locales'
import router from './router'
import store from './store'
import App from './App.vue'

const app = createApp(App);

app.use(store);
app.use(router);
app.use(ElementPlus);
app.use(i18n);
app.use(scui);

// 开发时：注入样式以临时隐藏 webpack-dev-server 的 overlay（用于在本地调试时避免错误覆盖层遮挡 UI）
if (process.env.NODE_ENV === 'development') {
	try {
		const style = document.createElement('style');
		style.setAttribute('data-dev-overlay-hide', 'true');
		style.innerHTML = `
			/* 隐藏 webpack dev overlay */
			#webpack-dev-server-client-overlay, .webpack-dev-server-client-overlay, .overlay, #ws-overlay { display: none !important; }
		`;
		document.head.appendChild(style);
		// 仅在控制台输出提示，便于调试
		console.debug('Injected dev overlay hide style');
	} catch (e) {
		// 忽略任何错误，确保不影响正常启动
	}
}

//挂载app
app.mount('#app');
