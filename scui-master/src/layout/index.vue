<template>
	<!-- 通栏布局 -->
	<template v-if="layout=='header'">
		<header class="adminui-header">
			<div class="adminui-header-left">
				<div class="logo-bar">
					<img class="logo" src="@/assets/images/logo.png">
					<span>{{ $CONFIG.APP_NAME }}</span>
				</div>
				<ul v-if="!ismobile" class="nav">
					<li v-for="item in menu" :key="item && item.path ? item.path : item" :class="pmenu.path==item.path?'active':''" @click="showMenu(item)">
						<el-icon><component :is="(item && item.meta && item.meta.icon) || 'el-icon-menu'" /></el-icon>
						<span>{{ (item && item.meta && item.meta.title) || '' }}</span>
					</li>
				</ul>
			</div>
			<div class="adminui-header-right">
				<userbar></userbar>
			</div>
		</header>
		<section class="aminui-wrapper">
			<div v-if="!ismobile && nextMenu.length>0 || !pmenu.component" :class="menuIsCollapse?'aminui-side isCollapse':'aminui-side'">
					<div v-if="!menuIsCollapse" class="adminui-side-top">
						<h2>{{ (pmenu && pmenu.meta && pmenu.meta.title) || '' }}</h2>
					</div>
				<div class="adminui-side-scroll">
					<el-scrollbar>
						<el-menu :default-active="active" router :collapse="menuIsCollapse" :unique-opened="$CONFIG.MENU_UNIQUE_OPENED">
							<NavMenu :navMenus="nextMenu"></NavMenu>
						</el-menu>
					</el-scrollbar>
				</div>
				<div class="adminui-side-bottom" @click="$store.commit('TOGGLE_menuIsCollapse')">
					<el-icon><el-icon-expand v-if="menuIsCollapse"/><el-icon-fold v-else /></el-icon>
				</div>
			</div>
			<Side-m v-if="ismobile"></Side-m>
			<div class="aminui-body el-container">
				<Topbar v-if="!ismobile"></Topbar>
				<Tags v-if="!ismobile && layoutTags"></Tags>
				<div class="adminui-main" id="adminui-main">
					<router-view v-slot="{ Component }">
					    <keep-alive :include="this.$store.state.keepAlive.keepLiveRoute">
					        <component :is="Component" :key="$route.fullPath" v-if="$store.state.keepAlive.routeShow"/>
					    </keep-alive>
					</router-view>
					<iframe-view></iframe-view>
				</div>
			</div>
		</section>
	</template>

	<!-- 经典布局 -->
	<template v-else-if="layout=='menu'">
		<header class="adminui-header">
			<div class="adminui-header-left">
				<div class="logo-bar">
					<img class="logo" src="@/assets/images/logo.png">
					<span>{{ $CONFIG.APP_NAME }}</span>
				</div>
			</div>
			<div class="adminui-header-right">
				<userbar></userbar>
			</div>
		</header>
		<section class="aminui-wrapper">
			<div v-if="!ismobile" :class="menuIsCollapse?'aminui-side isCollapse':'aminui-side'">
				<div class="adminui-side-scroll">
					<el-scrollbar>
						<el-menu :default-active="active" router :collapse="menuIsCollapse" :unique-opened="$CONFIG.MENU_UNIQUE_OPENED">
							<NavMenu :navMenus="menu"></NavMenu>
						</el-menu>
					</el-scrollbar>
				</div>
				<div class="adminui-side-bottom" @click="$store.commit('TOGGLE_menuIsCollapse')">
					<el-icon><el-icon-expand v-if="menuIsCollapse"/><el-icon-fold v-else /></el-icon>
				</div>
			</div>
			<Side-m v-if="ismobile"></Side-m>
			<div class="aminui-body el-container">
				<Topbar v-if="!ismobile"></Topbar>
				<Tags v-if="!ismobile && layoutTags"></Tags>
				<div class="adminui-main" id="adminui-main">
					<router-view v-slot="{ Component }">
					    <keep-alive :include="this.$store.state.keepAlive.keepLiveRoute">
					        <component :is="Component" :key="$route.fullPath" v-if="$store.state.keepAlive.routeShow"/>
					    </keep-alive>
					</router-view>
					<iframe-view></iframe-view>
				</div>
			</div>
		</section>
	</template>

	<!-- 功能坞布局 -->
	<template v-else-if="layout=='dock'">
		<header class="adminui-header">
			<div class="adminui-header-left">
				<div class="logo-bar">
					<img class="logo" src="@/assets/images/logo.png">
					<span>{{ $CONFIG.APP_NAME }}</span>
				</div>
			</div>
			<div class="adminui-header-right">
				<div v-if="!ismobile" class="adminui-header-menu">
					<el-menu mode="horizontal" :default-active="active" router background-color="#222b45" text-color="#fff" active-text-color="var(--el-color-primary)">
						<NavMenu :navMenus="menu"></NavMenu>
					</el-menu>
				</div>
				<Side-m v-if="ismobile"></Side-m>
				<userbar></userbar>
			</div>
		</header>
		<section class="aminui-wrapper">
			<div class="aminui-body el-container">
				<Tags v-if="!ismobile && layoutTags"></Tags>
				<div class="adminui-main" id="adminui-main">
					<router-view v-slot="{ Component }">
					    <keep-alive :include="this.$store.state.keepAlive.keepLiveRoute">
					        <component :is="Component" :key="$route.fullPath" v-if="$store.state.keepAlive.routeShow"/>
					    </keep-alive>
					</router-view>
					<iframe-view></iframe-view>
				</div>
			</div>
		</section>
	</template>

	<!-- 默认布局 -->
	<template v-else>
		<section class="aminui-wrapper">
			<div v-if="!ismobile" class="aminui-side-split">
				<div class="aminui-side-split-top">
					<router-link :to="$CONFIG.DASHBOARD_URL">
						<img class="logo" :title="$CONFIG.APP_NAME" src="@/assets/images/logo-r.png">
					</router-link>
				</div>
				<div class="adminui-side-split-scroll">
					<el-scrollbar>
						<ul>
							<li v-for="item in menu" :key="item" :class="pmenu.path==item.path?'active':''"
								@click="showMenu(item)">
								<el-icon><component :is="item.meta.icon || el-icon-menu" /></el-icon>
								<p>{{ (item && item.meta && item.meta.title) || '' }}</p>
							</li>
						</ul>
					</el-scrollbar>
				</div>
			</div>
			<div v-if="!ismobile && nextMenu.length>0 || !pmenu.component" :class="menuIsCollapse?'aminui-side isCollapse':'aminui-side'">
				<div v-if="!menuIsCollapse" class="adminui-side-top">
					<h2>{{ (pmenu && pmenu.meta && pmenu.meta.title) || '' }}</h2>
				</div>
				<div class="adminui-side-scroll">
					<el-scrollbar>
						<el-menu :default-active="active" router :collapse="menuIsCollapse" :unique-opened="$CONFIG.MENU_UNIQUE_OPENED">
							<NavMenu :navMenus="nextMenu"></NavMenu>
						</el-menu>
					</el-scrollbar>
				</div>
				<div class="adminui-side-bottom" @click="$store.commit('TOGGLE_menuIsCollapse')">
					<el-icon><el-icon-expand v-if="menuIsCollapse"/><el-icon-fold v-else /></el-icon>
				</div>
			</div>
			<Side-m v-if="ismobile"></Side-m>
			<div class="aminui-body el-container">
				<Topbar>
					<userbar></userbar>
				</Topbar>
				<Tags v-if="!ismobile && layoutTags"></Tags>
				<div class="adminui-main" id="adminui-main">
					<router-view v-slot="{ Component }">
					    <keep-alive :include="this.$store.state.keepAlive.keepLiveRoute">
					        <component :is="Component" :key="$route.fullPath" v-if="$store.state.keepAlive.routeShow"/>
					    </keep-alive>
					</router-view>
					<iframe-view></iframe-view>
				</div>
			</div>
		</section>
	</template>

	<div class="main-maximize-exit" @click="exitMaximize"><el-icon><el-icon-close /></el-icon></div>

	<div class="layout-setting" @click="openSetting"><el-icon><el-icon-brush-filled /></el-icon></div>

	<el-drawer title="布局实时演示" v-model="settingDialog" :size="400" append-to-body destroy-on-close>
		<setting></setting>
	</el-drawer>

	<auto-exit></auto-exit>
</template>

<script>
	import SideM from './components/sideM.vue';
	import Topbar from './components/topbar.vue';
	import Tags from './components/tags.vue';
	import NavMenu from './components/NavMenu.vue';
	import userbar from './components/userbar.vue';
	import setting from './components/setting.vue';
	import iframeView from './components/iframeView.vue';
	import autoExit from './other/autoExit.js';

	export default {
		name: 'index',
		components: {
			SideM,
			Topbar,
			Tags,
			NavMenu,
			userbar,
			setting,
			iframeView,
			autoExit
		},
		data() {
			return {
				settingDialog: false,
				menu: [],
				nextMenu: [],
				pmenu: {},
				active: ''
			}
		},
		computed:{
			ismobile(){
				return this.$store.state.global.ismobile
			},
			layout(){
				return this.$store.state.global.layout
			},
			layoutTags(){
				return this.$store.state.global.layoutTags
			},
			menuIsCollapse(){
				return this.$store.state.global.menuIsCollapse
			}
		},
		created() {
			this.onLayoutResize();
			// 添加防抖处理，避免短时间内大量触发导致布局抖动
			this._layoutResizeTimer = null;
			this._layoutResizeHandler = () => {
				if(this._layoutResizeTimer) clearTimeout(this._layoutResizeTimer);
				this._layoutResizeTimer = setTimeout(() => {
					this.onLayoutResize();
					this._layoutResizeTimer = null;
				}, 120);
			};
			window.addEventListener('resize', this._layoutResizeHandler);
			var menu = this.$router.sc_getMenu();
			this.menu = this.filterUrl(menu);
			// 如果后端或注入未提供 menu，尝试从 router.getRoutes() 生成一个备选 dashboard 菜单
			if((!this.menu || this.menu.length===0) && this.$router && this.$router.getRoutes){
				try{
					const routes = this.$router.getRoutes();
					const dashboardChildren = routes
						.filter(r=> r.path && r.path.startsWith('/dashboard/') && r.name)
						.map(r=>({ name: r.name, path: r.path, meta: r.meta || {}, component: (r.components && r.components.default) ? r.components.default : undefined }))
					if(dashboardChildren && dashboardChildren.length){
						this.menu = [{ name: 'dashboard', path: '/dashboard', component: 'dashboard/index', meta: { title: '首页' }, children: dashboardChildren }]
						console.info('[layout] built fallback menu from router.getRoutes:', this.menu.length)
					}
				}catch(e){ console.debug('[layout] build fallback menu failed', e) }
			}
			console.info('[layout] created menu length:', this.menu.length, 'userInfo:', this.$TOOL.data.get('USER_INFO'))
			// send runtime menu and user info to backend debug endpoint for diagnosis
			try{
				const payload = {
					menu: this.menu,
					userInfo: this.$TOOL.data.get('USER_INFO') || null
				}
				const base = this.$CONFIG.API_URL || ''
				let url = ''
				if(!base){
					url = '/api/debug/client-menu'
				}else if(base.endsWith('/api')){
					url = base.replace(/\/$/, '') + '/debug/client-menu'
				}else{
					url = base.replace(/\/$/, '') + '/api/debug/client-menu'
				}
				fetch(url, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify(payload)
				}).catch(()=>{})
			}catch(e){ console.debug('[layout] debug post failed', e) }
			this.showThis()
		},
		watch: {
			$route() {
				this.showThis()
			},
			layout: {
				handler(val){
					document.body.setAttribute('data-layout', val)
				},
				immediate: true,
			}
		},
		beforeUnmount(){
			try{
				window.removeEventListener('resize', this._layoutResizeHandler);
			}catch(e){
				// 忽略可能的异常（例如 handler 未绑定）并记录以便调试
				console.debug('[layout] removeEventListener error', e)
			}
			if(this._layoutResizeTimer){
				clearTimeout(this._layoutResizeTimer);
				this._layoutResizeTimer = null;
			}

		},
		methods: {
			openSetting(){
				this.settingDialog = true;
			},
			onLayoutResize(){
				this.$store.commit("SET_ismobile", document.body.clientWidth < 992)
			},
			//路由监听高亮
			showThis(){
				this.pmenu = this.$route.meta.breadcrumb ? this.$route.meta.breadcrumb[0] : {}
				this.nextMenu = this.filterUrl(this.pmenu.children);
				// If breadcrumb-based pmenu produced no children, fallback to searching stored menu by path
				if((!this.nextMenu || this.nextMenu.length==0) && this.menu && this.menu.length>0){
					const findParent = (nodes, path) => {
						for(let n of nodes){
							if(n.path === path) return n
							if(n.children && n.children.length){
								let ch = n.children.find(c=> c.path === path)
								if(ch) return n
								let rec = findParent(n.children, path)
								if(rec) return rec
							}
						}
						return null
					}
					let fallback = findParent(this.menu, this.$route.path)
					if(fallback){
						this.pmenu = fallback
						this.nextMenu = this.filterUrl(this.pmenu.children)
					}
				}

				// Post debug snapshot of current pmenu/nextMenu to backend (non-blocking)
				try{
					const payload = { path: this.$route.path, pmenu: this.pmenu, nextMenu: this.nextMenu }
					const base = this.$CONFIG.API_URL || ''
					let url = ''
					if(!base){
						url = '/api/debug/client-menu'
					}else if(base.endsWith('/api')){
						url = base.replace(/\/$/, '') + '/debug/client-menu'
					}else{
						url = base.replace(/\/$/, '') + '/api/debug/client-menu'
					}
					fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }).catch(()=>{})
				}catch(e){ console.debug('[layout] showThis debug post failed', e) }
				this.$nextTick(()=>{
					this.active = this.$route.meta.active || this.$route.fullPath;
				})
			},
			//点击显示
			showMenu(route) {
				this.pmenu = route;
				this.nextMenu = this.filterUrl(route.children);
				if((!route.children || route.children.length == 0) && route.component){
					this.$router.push({path: route.path})
				}
			},
			//转换外部链接的路由
			filterUrl(map){
				var newMap = []
				map && map.forEach(item => {
					item.meta = item.meta?item.meta:{};
					//处理隐藏
					if(item.meta.hidden || item.meta.type=="button"){
						return false
					}
					//处理http
					if(item.meta.type=='iframe'){
						item.path = `/i/${item.name}`;
					}
					//递归循环
					if(item.children&&item.children.length > 0){
						item.children = this.filterUrl(item.children)
					}
					newMap.push(item)
				})
				return newMap;
			},
			//退出最大化
			exitMaximize(){
				document.getElementById('app').classList.remove('main-maximize')
			}
		}
	}
</script>


<style scoped>
/* Improve aminui-side visual spacing and active indicator */
.aminui-side .adminui-side-scroll { padding-top: 8px }
.aminui-side .el-menu-item, .aminui-side .el-sub-menu__title { padding-left: 20px !important }
.aminui-side .el-menu-item .el-icon, .aminui-side .el-sub-menu__title .el-icon { margin-right: 10px }
.aminui-side .el-menu-item.is-active, .aminui-side .el-sub-menu__title.is-active { background: rgba(52,152,219,0.06) !important; color: var(--el-color-primary) !important; font-weight: 600 }
.aminui-side .el-menu-item.is-active::before, .aminui-side .el-sub-menu__title.is-active::before { left: 12px }
.aminui-side.isCollapse .el-menu-item::before, .aminui-side.isCollapse .el-sub-menu__title::before { display: none }

/* Slightly increase dashboard header spacing */
.adminui-side-top h2 { margin: 12px 16px; font-size: 18px }

/* Main content padding and responsive container */
.adminui-main { padding: 20px; background: var(--el-bg-color-page); min-height: calc(100vh - 140px); box-sizing: border-box; }
.aminui-body .adminui-main { max-width: none; margin: 0; width: 100%; padding-left: 24px; padding-right: 24px; }

/* Ensure smaller screens keep comfortable padding */
@media (max-width: 991px) {
	.adminui-main { padding: 12px }
}

</style>


