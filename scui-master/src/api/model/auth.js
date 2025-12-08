import http from "@/utils/request"

export default {
	token: {
		// use a relative path so axios baseURL (sysConfig.API_URL) is applied once
		url: `/token`,
		name: "登录获取TOKEN",
		post: async function(data={}){
			return await http.post(this.url, data);
		}
	}
}
