<template>
	<div class="login-wrapper password-form-root">
		<el-form ref="loginForm" :model="form" :rules="rules" label-width="0" size="large" @keyup.enter="login">
			<el-form-item prop="user">
				<el-input v-model="form.user" prefix-icon="el-icon-user" clearable :placeholder="$t('login.userPlaceholder')">
					<template #append>
						<el-select v-model="userType" style="width: 130px;">
							<el-option :label="$t('login.admin')" value="admin"></el-option>
							<el-option :label="$t('login.user')" value="user"></el-option>
						</el-select>
					</template>
				</el-input>
			</el-form-item>
			<el-form-item prop="password">
				<el-input v-model="form.password" prefix-icon="el-icon-lock" clearable show-password :placeholder="$t('login.PWPlaceholder')"></el-input>
			</el-form-item>
			<el-form-item style="margin-bottom: 10px;">
				<el-col :span="12">
					<el-checkbox :label="$t('login.rememberMe')" v-model="form.autologin"></el-checkbox>
				</el-col>
				<el-col :span="12" class="login-forgot">
					<router-link to="/reset_password">{{ $t('login.forgetPassword') }}？</router-link>
				</el-col>
			</el-form-item>
			<el-form-item>
				<el-button type="primary" style="width: 100%;" :loading="islogin" round @click="login">{{ $t('login.signIn') }}</el-button>
			</el-form-item>
			<div class="login-reg">
				{{$t('login.noAccount')}} <router-link to="/user_register">{{$t('login.createAccount')}}</router-link>
			</div>
		</el-form>
		<!-- initialization overlay shown while routes are injected and we navigate -->
		<div v-if="initializing" class="login-overlay">
			<div class="login-overlay-box">
				<div class="lds-ring"><div></div><div></div><div></div><div></div></div>
				<div class="login-overlay-text">正在初始化，请稍候…</div>
			</div>
		</div>
	</div>
</template>

<script>
	export default {
		data() {
			return {
				initializing: false,
				userType: 'admin',
				form: {
					user: "admin",
					password: "admin",
					autologin: false
				},
				rules: {
					user: [
						{required: true, message: this.$t('login.userError'), trigger: 'blur'}
					],
					password: [
						{required: true, message: this.$t('login.PWError'), trigger: 'blur'}
					]
				},
				islogin: false,
			}
		},
		watch:{
			userType(val){
				if(val == 'admin'){
					this.form.user = 'admin'
					this.form.password = 'admin'
				}else if(val == 'user'){
					this.form.user = 'user'
					this.form.password = 'user'
				}
			}
		},
		mounted() {

		},
		methods: {
			async login(){

				var validate = await this.$refs.loginForm.validate().catch(()=>{})
				if(!validate){ return false }

				this.islogin = true
				var data = {
					username: this.form.user,
					password: this.form.password
				}
				//获取token
				var user = await this.$API.auth.token.post(data)
				// 兼容后端直接返回token和userInfo
				if(user.token && user.userInfo){
					this.$TOOL.cookie.set("TOKEN", user.token, {
						expires: this.form.autologin? 24*60*60 : 0,
						path: '/'
					})
					this.$TOOL.data.set("USER_INFO", user.userInfo)
				}else if(user.code == 200 && user.data && user.data.token){
					this.$TOOL.cookie.set("TOKEN", user.data.token, {
						expires: this.form.autologin? 24*60*60 : 0,
						path: '/'
					})
					this.$TOOL.data.set("USER_INFO", user.data.userInfo)
				}else{
					this.islogin = false
					this.$message.warning(user.message || '登录失败')
					return false
				}
				//获取菜单
				var menu = null
				if(this.form.user == 'admin'){
					menu = await this.$API.system.menu.myMenus.get()
				}else{
					menu = await this.$API.demo.menu.get()
				}
				console.debug('[login] fetched menu raw:', menu)
				if(menu.code == 200){
					let menuList = Array.isArray(menu.data) ? menu.data : menu.data.menu
					console.debug('[login] computed menuList:', menuList)
					if(!menuList || menuList.length==0){
						this.islogin = false
						this.$alert("当前用户无任何菜单权限，请联系系统管理员", "无权限访问", {
							type: 'error',
							center: true
						})
						return false
					}
					this.$TOOL.data.set("MENU", menuList)
					// also save an unhashed debug copy so we can verify storage immediately
					try{
						localStorage.setItem('MENU_DEBUG', JSON.stringify(menuList))
					}catch(e){console.debug('[login] MENU_DEBUG write failed', e)}
					// give a small delay to avoid race between saving and router dynamic registration
					await new Promise(res=>setTimeout(res, 120))
					// mark initializing to show overlay until injection+navigation complete
					this.initializing = true
					// Synchronously convert menu -> route objects and inject into router to avoid race
					try{
						const loadComponent = (component) => {
							if(!component) return () => import('@/layout/other/empty')
							return () => import(/* webpackChunkName: "[request]" */ `@/views/${component}`)
								.catch(()=> import(/* webpackChunkName: "[request]" */ `@/views/${component}/index`))
								.catch(()=> import('@/layout/other/empty'))
						}

						const convert = (item) => {
							// sanitize component and path: remove newlines/extra spaces and strip leading /scui
							const rawComp = (item.component || '')
							const comp = rawComp.replace(/\r|\n/g, '').trim()
							let path = item.path || ''
							if(path.startsWith('/scui')) path = path.replace(/^\/scui/, '') || '/'
							const route = {
								path: path,
								name: item.name,
								meta: item.meta || {},
								redirect: item.redirect,
								component: loadComponent(comp)
							}
							if(item.children && item.children.length){
								route.children = item.children.map(convert)
							}
							return route
						}

						let routesToAdd = menuList.map(convert)
						routesToAdd.forEach(r => {
							try{ this.$router.addRoute('layout', r) }catch(e){ console.debug('[login] addRoute failed', e) }
						})
						console.info('[login] injected routes count:', routesToAdd.length)
					}catch(e){ console.debug('[login] sync route injection failed', e)
						this.initializing = false
						// on injection failure, POST a detailed debug snapshot to server for diagnosis
						try{
							const errSnap = { error: String(e), menu: menuList, userInfo: this.$TOOL.data.get('USER_INFO'), routes: this.$router.getRoutes().map(r=>({name:r.name,path:r.path})) }
							fetch((this.$CONFIG && this.$CONFIG.API_PREFIX ? this.$CONFIG.API_PREFIX : '') + '/api/debug/client-menu', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(errSnap)}).catch(()=>{})
						}catch(_e){console.debug('[login] post err snapshot failed', _e)}
					}
					console.debug('[login] saved MENU to storage')
					console.info('[login] MENU_DEBUG saved, items:', menuList ? menuList.length : 0)
					this.$TOOL.data.set("PERMISSIONS", menu.data.permissions || [])
					this.$TOOL.data.set("DASHBOARDGRID", menu.data.dashboardGrid || [])

						// POST a debug snapshot to backend so server-side can record client state
						try{
							const snap = {
								menu: menuList,
								userInfo: this.$TOOL.data.get('USER_INFO'),
								routes: this.$router.getRoutes().map(r => ({name: r.name, path: r.path, meta: r.meta}))
							}
							fetch((this.$CONFIG && this.$CONFIG.API_PREFIX ? this.$CONFIG.API_PREFIX : '') + '/api/debug/client-menu', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(snap)}).catch(()=>{})
						}catch(e){console.debug('[login] debug snapshot post failed', e)}
				}else{
					this.islogin = false
					this.$message.warning(menu.message)
					return false
				}

				// navigate to dashboard (no full reload)
				const dash = (this.$CONFIG && this.$CONFIG.DASHBOARD_URL) ? this.$CONFIG.DASHBOARD_URL : '/dashboard'
				this.$router.replace({ path: dash }).catch(()=>{})
				this.$message.success("Login Success 登录成功")
				this.islogin = false
				this.initializing = false
			},
		}
	}
</script>

<style scoped>
.login-overlay{ position: absolute; left:0; right:0; top:0; bottom:0; background: rgba(255,255,255,0.85); display:flex; align-items:center; justify-content:center; z-index:9999 }
.login-overlay-box{ text-align:center }
.login-overlay-text{ margin-top:12px; color:#666 }
.lds-ring{ display:inline-block; width:48px; height:48px; position:relative }
.lds-ring div{ box-sizing: border-box; display:block; position:absolute; width:38px; height:38px; margin:6px; border:4px solid #3498db; border-radius:50%; animation: lds-ring 1.2s cubic-bezier(0.5,0,0.5,1) infinite; border-color:#3498db transparent transparent transparent }
.lds-ring div:nth-child(1){ animation-delay:-0.45s }
.lds-ring div:nth-child(2){ animation-delay:-0.3s }
.lds-ring div:nth-child(3){ animation-delay:-0.15s }
@keyframes lds-ring{ 0%{ transform: rotate(0deg) } 100%{ transform: rotate(360deg) } }

/* Ensure these login-form related styles override parent/global styles */
.password-form-root .login-forgot { text-align: right; }
.password-form-root .login-forgot a { color: var(--el-color-primary); }
.password-form-root .login-forgot a:hover { color: var(--el-color-primary-light-3); }
.password-form-root .login-reg { font-size: 14px; color: var(--el-text-color-primary); }
.password-form-root .login-reg a { color: var(--el-color-primary); }
.password-form-root .login-reg a:hover { color: var(--el-color-primary-light-3); }

/* Additional overrides to ensure layout and controls display correctly */
.password-form-root { width: 100%; }
.password-form-root .el-form { width: 100%; }
.password-form-root .el-button { width: 100% !important; }
.password-form-root .el-input__inner { box-sizing: border-box; }
.password-form-root .login-overlay { z-index: 9999; }


</style>
