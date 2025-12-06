import { createRouter, createWebHistory } from 'vue-router';
import { ElNotification } from 'element-plus';
import config from "@/config"
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import tool from '@/utils/tool';
import systemRouter from './systemRouter';
import userRoutes from '@/config/route';
import {beforeEach, afterEach} from './scrollBehavior';

//系统路由
const routes = systemRouter

//系统特殊路由
const routes_404 = {
	path: "/:pathMatch(.*)*",
	hidden: true,
	  component: () => import(/* webpackChunkName: "404" */ '@/layout/other/404'),
}
let routes_404_r = ()=>{}

const router = createRouter({
	history: createWebHistory(process.env.VUE_APP_PUBLIC_PATH),
	routes: routes
})

//设置标题
document.title = config.APP_NAME

//判断是否已加载过动态/静态路由
var isGetRouter = false;

// Listener: allow login to synchronously trigger menu-ready route injection
window.addEventListener && window.addEventListener('MENU_READY', (e) => {
	try{
		console.info('[router] MENU_READY event received')
		if(isGetRouter) return
		const payload = e && e.detail ? e.detail : {}
		console.info('[router] MENU_READY payload:', payload && payload.menu ? payload.menu.length : 0, 'items')
		const apiMenu = payload.menu || (tool.data.get('MENU') || [])
		const userInfo = payload.userInfo || tool.data.get('USER_INFO') || { role: [] }
		const userRoleArray = Array.isArray(userInfo.role) ? userInfo.role : []
		// When configured to use backend-driven menus, prefer apiMenu exclusively.
		// Only fall back to filtered static userRoutes if apiMenu is empty.
		let menu = (apiMenu && apiMenu.length) ? apiMenu : treeFilter(userRoutes, node => {
			if (!node.meta || !node.meta.role) return true
			return node.meta.role.filter(item => userRoleArray.indexOf(item) > -1).length > 0
		})
		var menuRouter = filterAsyncRouter(menu)
		menuRouter = flatAsyncRoutes(menuRouter)
		menuRouter.forEach(item => {
			router.addRoute("layout", item)
		})
		console.info('[router] MENU_READY injected routes count:', menuRouter.length)
		// after injecting routes, try to re-evaluate the current route so breadcrumb/meta update
		try{
			const cur = router.currentRoute
			if(cur && cur.value && cur.value.matched && cur.value.matched.length === 0){
				router.replace(cur.value.fullPath).catch(()=>{})
				console.info('[router] post-inject replace called')
			}
		}catch(e){ console.debug('[router] post-inject replace failed', e) }
		routes_404_r = router.addRoute(routes_404)
		isGetRouter = true
	}catch(err){ console.debug('[router] MENU_READY handler failed', err) }
})

// Expose synchronous route init so login can call directly when available
window.__SCUI_ROUTE_INIT = function(payload){
	try{
		console.info('[router] __SCUI_ROUTE_INIT called')
		if(isGetRouter) return
	console.info('[router] __SCUI_ROUTE_INIT payload:', payload && payload.menu ? payload.menu.length : 0, 'items')
	// Prefer backend-provided menu only
	const apiMenu = payload && payload.menu ? payload.menu : (tool.data.get('MENU') || [])
		const userInfo = payload && payload.userInfo ? payload.userInfo : (tool.data.get('USER_INFO') || { role: [] })
		const userRoleArray = Array.isArray(userInfo.role) ? userInfo.role : []
		// Use only apiMenu when available, otherwise fall back to userMenu
		let menu = (apiMenu && apiMenu.length) ? apiMenu : treeFilter(userRoutes, node => {
			if (!node.meta || !node.meta.role) return true
			return node.meta.role.filter(item => userRoleArray.indexOf(item) > -1).length > 0
		})
		var menuRouter = filterAsyncRouter(menu)
		menuRouter = flatAsyncRoutes(menuRouter)
		menuRouter.forEach(item => {
			router.addRoute("layout", item)
		})
		console.info('[router] __SCUI_ROUTE_INIT injected routes count:', menuRouter.length)
		// after injecting routes, try to re-evaluate the current route so breadcrumb/meta update
		try{
			const cur = router.currentRoute
			if(cur && cur.value && cur.value.matched && cur.value.matched.length === 0){
				router.replace(cur.value.fullPath).catch(()=>{})
				console.info('[router] post-init replace called')
			}
		}catch(e){ console.debug('[router] post-init replace failed', e) }
		routes_404_r = router.addRoute(routes_404)
		isGetRouter = true
	}catch(err){ console.debug('[router] __SCUI_ROUTE_INIT failed', err) }
}

router.beforeEach(async (to, from, next) => {

	NProgress.start()
	//动态标题
	document.title = (to && to.meta && to.meta.title) ? `${to.meta.title} - ${config.APP_NAME}` : `${config.APP_NAME}`

	let token = tool.cookie.get("TOKEN");

	if(to.path === "/login"){
		//删除路由(替换当前layout路由)
		router.addRoute(routes[0])
		//删除路由(404)
		routes_404_r()
		isGetRouter = false;
		next();
		return false;
	}

	if(routes.findIndex(r => r.path === to.path) >= 0){
		next();
		return false;
	}

	if(!token){
		next({
			path: '/login'
		});
		return false;
	}

	//整页路由处理
	if(to.meta.fullpage){
		to.matched = [to.matched[to.matched.length-1]]
	}
	//加载动态/静态路由
	if(!isGetRouter){
			let apiMenu = tool.data.get("MENU") || []
			// If MENU is empty, try to fetch from backend synchronously (best-effort)
			if((!apiMenu || apiMenu.length==0) && tool.cookie.get('TOKEN')){
				try{
					// use the same API that login uses
					fetch((config.API_URL||'') + '/system/menu/my/1.6.1', { headers: { 'Content-Type': 'application/json', 'Authorization': config.TOKEN_PREFIX + tool.cookie.get('TOKEN') } })
						.then(r=>r.json()).then(m=>{
							let menuList = Array.isArray(m.data) ? m.data : (m.data? m.data.menu : [])
							if(menuList && menuList.length>0){
								tool.data.set('MENU', menuList)
								apiMenu = menuList
							}
						}).catch(()=>{})
				}catch(e){console.debug('[router] fetch menu fallback failed', e)}
			}
		// Ensure userInfo exists and has a role array to avoid runtime errors when not logged in
		let userInfo = tool.data.get("USER_INFO") || { role: [] }
		let userRoleArray = Array.isArray(userInfo.role) ? userInfo.role : []
		// Use only apiMenu when provided; fall back to filtered static userRoutes if not
		let menu = (apiMenu && apiMenu.length) ? apiMenu : treeFilter(userRoutes, node => {
			if (!node.meta || !node.meta.role) return true
			return node.meta.role.filter(item => userRoleArray.indexOf(item) > -1).length > 0
		})
		var menuRouter = filterAsyncRouter(menu)
		menuRouter = flatAsyncRoutes(menuRouter)

			// Debug: POST the computed menu and apiMenu to backend for inspection (non-blocking)
			try{
				const payload = { apiMenu: apiMenu, menu: menu, userInfo: tool.data.get('USER_INFO') || null }
				const base = config.API_URL || ''
				let url = ''
				if(!base){
					url = '/api/debug/client-menu'
				}else if(base.endsWith('/api')){
					url = base.replace(/\/$/, '') + '/debug/client-menu'
				}else{
					url = base.replace(/\/$/, '') + '/api/debug/client-menu'
				}
				fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }).catch(()=>{})
			}catch(e){ console.debug('[router] debug post failed', e) }

		menuRouter.forEach(item => {
			router.addRoute("layout", item)
		})
		routes_404_r = router.addRoute(routes_404)
		// after injecting routes, if current target had no match, try re-pushing to re-evaluate
		try{
			if (to.matched.length == 0) {
				router.push(to.fullPath).catch(()=>{})
				console.info('[router] post-beforeEach push called')
			}
		}catch(e){ console.debug('[router] post-beforeEach push failed', e) }
		isGetRouter = true;
	}
	beforeEach(to, from)
	next();
});

router.afterEach((to, from) => {
	afterEach(to, from)
	NProgress.done()
});

router.onError((error) => {
	NProgress.done();
	ElNotification.error({
		title: '路由错误',
		message: error.message
	});
});

//入侵追加自定义方法、对象
router.sc_getMenu = () => {
	var apiMenu = tool.data.get("MENU") || []
	let userInfo = tool.data.get("USER_INFO") || { role: [] }
	let userRoleArray = Array.isArray(userInfo.role) ? userInfo.role : []
	let userMenu = treeFilter(userRoutes, node => {
		if (!node.meta || !node.meta.role) return true
		return node.meta.role.filter(item => userRoleArray.indexOf(item) > -1).length > 0
	})
	// Prefer apiMenu (server-provided menu with meta/icon). If apiMenu is empty,
	// fall back to the filtered static userMenu. This uses both variables and
	// satisfies the linter.
	return (apiMenu && apiMenu.length) ? apiMenu : userMenu
}

//转换
function filterAsyncRouter(routerMap) {
	const accessedRouters = []
	routerMap.forEach(item => {
		item.meta = item.meta?item.meta:{};
		//处理外部链接特殊路由
		if(item.meta.type=='iframe'){
			item.meta.url = item.path;
			item.path = `/i/${item.name}`;
		}
		//MAP转路由对象
		var route = {
			path: item.path,
			name: item.name,
			meta: item.meta,
			redirect: item.redirect,
			children: item.children ? filterAsyncRouter(item.children) : null,
			component: loadComponent(item.component)
		}
		accessedRouters.push(route)
	})
	return accessedRouters
}
function loadComponent(component){
	if(component){
		// Try importing the exact component path first. If that fails (path points to a folder),
		// try the /index variant. If both fail, fall back to an empty placeholder component.
		return () => import(/* webpackChunkName: "[request]" */ `@/views/${component}`)
			.catch(err => {
				// attempt fallback to index within folder
				return import(/* webpackChunkName: "[request]" */ `@/views/${component}/index`)
					.catch(err2 => {
						console.warn('[router] loadComponent failed for', component, err, err2)
						return import(`@/layout/other/empty`)
					})
			})
	}else{
		return () => import(`@/layout/other/empty`)
	}

}

//路由扁平化
function flatAsyncRoutes(routes, breadcrumb=[]) {
	let res = []
	routes.forEach(route => {
		const tmp = {...route}
        if (tmp.children) {
            let childrenBreadcrumb = [...breadcrumb]
            childrenBreadcrumb.push(route)
            let tmpRoute = { ...route }
            tmpRoute.meta.breadcrumb = childrenBreadcrumb
            delete tmpRoute.children
            res.push(tmpRoute)
            let childrenRoutes = flatAsyncRoutes(tmp.children, childrenBreadcrumb)
            childrenRoutes.map(item => {
                res.push(item)
            })
        } else {
            let tmpBreadcrumb = [...breadcrumb]
            tmpBreadcrumb.push(tmp)
            tmp.meta.breadcrumb = tmpBreadcrumb
            res.push(tmp)
        }
    })
    return res
}

//过滤树
function treeFilter(tree, func) {
	return tree.map(node => ({ ...node })).filter(node => {
		node.children = node.children && treeFilter(node.children, func)
		return func(node) || (node.children && node.children.length)
	})
}

export default router
