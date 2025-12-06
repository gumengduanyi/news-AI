<template>
	<div ref="scEcharts" :style="{height:height, width:width}"></div>
</template>

<script>
	import * as echarts from 'echarts';
	import T from './echarts-theme-T.js';
	echarts.registerTheme('T', T);
	const unwarp = (obj) => obj && (obj.__v_raw || obj.valueOf() || obj);

	export default {
		...echarts,
		name: "scEcharts",
		props: {
			height: { type: String, default: "100%" },
			width: { type: String, default: "100%" },
			nodata: {type: Boolean, default: false },
			option: { type: Object, default: () => {} }
		},
		data() {
			return {
				isActivat: false,
				myChart: null
			}
		},
		watch: {
			option: {
				deep:true,
				handler (v) {
					unwarp(this.myChart).setOption(v);
				}
			}
		},
		computed: {
			myOptions: function() {
				return this.option || {};
			}
		},
		activated(){
			if(!this.isActivat){
				this.$nextTick(() => {
					this.myChart.resize()
				})
			}
		},
		deactivated(){
			this.isActivat = false;
		},
		beforeUnmount(){
			try{
				window.removeEventListener('resize', this._scEchartsResizeHandler);
			}catch(e){ console.debug('[scEcharts] resize error', e) }
			if(this._scEchartsResizeTimer) {
				clearTimeout(this._scEchartsResizeTimer);
				this._scEchartsResizeTimer = null;
			}
		},
		mounted(){
			this.isActivat = true;
			this.$nextTick(() => {
				this.draw();
			})
		},
		methods: {
			draw(){
				var myChart = echarts.init(this.$refs.scEcharts, 'T');
				myChart.setOption(this.myOptions);
				this.myChart = myChart;
				// 使用防抖来减少 resize 事件触发频率，避免引起 ResizeObserver loop
				this._scEchartsResizeTimer = null;
				this._scEchartsResizeHandler = () => {
					if(this._scEchartsResizeTimer) clearTimeout(this._scEchartsResizeTimer);
					this._scEchartsResizeTimer = setTimeout(() => {
						try{ myChart.resize(); }catch(e){ console.debug('[scEcharts] myChart.resize error', e) }
						this._scEchartsResizeTimer = null;
					}, 120);
				};
				window.addEventListener('resize', this._scEchartsResizeHandler);
			}
		}
	}
</script>
