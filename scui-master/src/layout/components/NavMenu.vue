<template>
	<div v-if="navMenus.length<=0" style="padding:20px;">
		<el-alert title="无子集菜单" center type="info" :closable="false"></el-alert>
	</div>
	<template v-for="navMenu in navMenus" v-bind:key="navMenu">
		<el-menu-item v-if="!hasChildren(navMenu)" :index="navMenu.path">
			<a v-if="navMenu.meta && navMenu.meta.type=='link'" :href="navMenu.path" target="_blank" @click.stop='()=>{}'></a>
			<el-icon>
				<!-- resolve icon (meta.icon or derived default), prefer resolved component (registered name or component object) -->
				<span v-if="getRenderableIcon(navMenu)">
					<component :is="getRenderableIcon(navMenu)" />
				</span>
				<el-icon v-else class="default-icon"><el-icon-menu /></el-icon>
			</el-icon>
			<template #title>
				<span>{{ (navMenu && navMenu.meta && navMenu.meta.title) || '' }}</span>
				<span v-if="navMenu.meta && navMenu.meta.tag" class="menu-tag">{{navMenu.meta.tag}}</span>
			</template>
		</el-menu-item>
		<el-sub-menu v-else :index="navMenu.path">
			<template #title>
				<el-icon>
					<span v-if="getRenderableIcon(navMenu)">
						<component :is="getRenderableIcon(navMenu)" />
					</span>
					<el-icon v-else class="default-icon"><el-icon-menu /></el-icon>
				</el-icon>
				<span>{{ (navMenu && navMenu.meta && navMenu.meta.title) || '' }}</span>
				<span v-if="navMenu.meta && navMenu.meta.tag" class="menu-tag">{{navMenu.meta.tag}}</span>
			</template>
			<NavMenu :navMenus="navMenu.children"></NavMenu>
		</el-sub-menu>
	</template>
</template>

<script>
import * as ElIcons from '@element-plus/icons-vue'
	export default {
		name: 'NavMenu',
		props: ['navMenus'],
		data() {
			return {}
		},
		methods: {
			hasChildren(item) {
				return item.children && !item.children.every(item => item.meta.hidden)
			}
			,isComponentIcon(name){
				if(!name || typeof name !== 'string') return false;
				const pascalCase = /^[A-Z][A-Za-z0-9_-]*$/;
				return pascalCase.test(name) || name.startsWith('ElIcon') || name.startsWith('ScIcon')
			},
			getIconComponent(name){
				if(!name || typeof name !== 'string') return '';
				// if already looks like a component name, return as-is
				if(this.isComponentIcon(name)) return name;
				// convert kebab-case el-icon-data-analysis -> ElIconDataAnalysis
				let m = name.match(/^(el-icon|sc-icon|el|sc)-?(.*)$/);
				if(m){
					const prefix = m[1];
					const rest = m[2] || '';
					const parts = rest.split(/[-_]/).filter(Boolean).map(p => p.charAt(0).toUpperCase() + p.slice(1));
					const comp = (prefix.startsWith('el')? 'ElIcon' : 'ScIcon') + parts.join('');
					return comp;
				}
				return '';
			},
				// Resolve an icon for a menu entry. If meta.icon exists return it;
				// otherwise derive from title keywords or fallback to a generic icon.
				getResolvedIcon(navMenu){
					if(!navMenu) return 'el-icon-menu';
					const meta = navMenu.meta || {};
					if(meta.icon) return meta.icon;
					const title = (meta.title || navMenu.name || navMenu.path || '').toString();
					const t = title.toLowerCase();
					// keyword -> preferred icon mapping (expanded)
					const mapping = [
						{keys: ['报','报告','生成','报表'], icon: 'el-icon-edit'},
						{keys: ['已生成','已生成报告','生成报告'], icon: 'el-icon-document'},
						{keys: ['采集','采集内容','抓取'], icon: 'el-icon-notebook-2'},
						{keys: ['输出','模板','导出'], icon: 'el-icon-upload'},
						{keys: ['模型','模型设置'], icon: 'el-icon-s-platform'},
						{keys: ['提示词','提示','提示管理'], icon: 'el-icon-s-management'},
						{keys: ['自动','发送','调度'], icon: 'el-icon-s-check'},
						{keys: ['任务','任务管理'], icon: 'el-icon-s-order'},
						{keys: ['日志','记录','审计'], icon: 'el-icon-time'},
						{keys: ['用户','成员','中心','个人'], icon: 'el-icon-user'},
						{keys: ['权限','角色','访问'], icon: 'el-icon-lock'},
						{keys: ['通知','告警','提醒'], icon: 'el-icon-bell'},
						{keys: ['审批','流程','工作流'], icon: 'el-icon-s-flag'},
						{keys: ['设置','配置','偏好'], icon: 'el-icon-setting'},
						{keys: ['搜索','查询'], icon: 'el-icon-search'}
					];
					for(const m of mapping){
						for(const k of m.keys){
							if(t.indexOf(k) !== -1) return m.icon;
						}
					}
					return 'el-icon-menu';
				},
				// Resolve a component to render: prefer global registration name,
				// otherwise try to find the component in the local ElIcons map.
				resolveComponent(compName){
					if(!compName) return null;
					try{
						const registry = this.$.appContext && this.$.appContext.components ? this.$.appContext.components : (this.$root && this.$root.$options && this.$root.$options.components ? this.$root.$options.components : {});
						if(registry[compName]) return compName; // string name is fine for <component :is>
						// fallback: try ElIcons exports using stripped name (ElIconXxx -> Xxx)
						if(typeof compName === 'string' && compName.startsWith('ElIcon')){
							const key = compName.slice('ElIcon'.length);
							if(ElIcons && ElIcons[key]) return ElIcons[key];
						}
						return null;
					}catch(e){
						return null;
					}
				},
				// Return a value usable by <component :is="...">: either a registered component name (string)
				// or a component object from ElIcons (function/object). Returns null when nothing found.
				getRenderableIcon(navMenu){
					const iconName = this.getResolvedIcon(navMenu);
					if(!iconName) return null;
					// If resolveComponent returns a component object or registered name, use it
					const resolved = this.resolveComponent(this.getIconComponent(iconName) || iconName);
					if(resolved) return resolved;
					// As a last attempt, if iconName is already like 'ElIconXxx', try ElIcons directly
					if(typeof iconName === 'string' && iconName.startsWith('ElIcon')){
						const key = iconName.slice('ElIcon'.length);
						if(ElIcons && ElIcons[key]) return ElIcons[key];
					}
					return null;
				},
			hasRegisteredComponent(compName){
				if(!compName) return false;
				// try to access app's registered components
				try{
					const registry = this.$.appContext && this.$.appContext.components ? this.$.appContext.components : (this.$root && this.$root.$options && this.$root.$options.components ? this.$root.$options.components : {});
					return !!registry[compName];
				}catch(e){
					return false;
				}
			}
		}
	}
</script>

<style scoped>
/* nav menu hover and active enhancements */
.el-menu-item, .el-sub-menu__title {
	transition: background-color .15s ease, color .15s ease;
	padding: 10px 18px !important;
}
.el-menu-item:hover, .el-sub-menu__title:hover {
	background-color: rgba(52,152,219,0.06) !important; /* subtle blue */
}
.el-menu-item.is-active > a, .el-menu-item.is-active, .el-sub-menu__title.is-active {
	background-color: rgba(52,152,219,0.09) !important;
	color: var(--el-color-primary) !important;
	font-weight: 600;
}
/* left accent bar for active item */
.el-menu-item.is-active::before, .el-sub-menu__title.is-active::before {
	content: '';
	position: absolute;
	left: 0;
	top: 6px;
	bottom: 6px;
	width: 3px;
	background: var(--el-color-primary);
	border-radius: 2px;
}

.el-menu-item, .el-sub-menu__title { position: relative }

.el-menu-item .el-icon, .el-sub-menu__title .el-icon { font-size: 18px; margin-right: 12px }

.menu-tag { margin-left: 8px; font-size: 12px }
</style>
