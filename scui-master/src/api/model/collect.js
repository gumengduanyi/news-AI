import config from "@/config"
import http from "@/utils/request"

export default {
  collect: {
    url: {
      url: `${config.API_URL}/collect/url`,
      name: "提交采集任务",
      post: async function(data) {
        return await http.post(this.url, data)
      }
    },
    input: {
      url: `${config.API_URL}/collect/input`,
      name: "手动录入",
      post: async function(data) {
        return await http.post(this.url, data)
      }
    },
    result: {
      url: `${config.API_URL}/collect/result`,
      name: "获取采集结果",
      get: async function(params) {
        return await http.get(this.url, params);
      }
    },
    remove: {
      url: `${config.API_URL}/collect/delete`,
      name: "删除采集结果",
      post: async function(data) {
        return await http.post(this.url, data)
      }
    }
  }
}
