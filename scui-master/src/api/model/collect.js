import http from "@/utils/request"

export default {
  collect: {
    url: {
      url: `/collect/url`,
      name: "提交采集任务",
      post: async function(data) {
        return await http.post(this.url, data)
      }
    },
    input: {
      url: `/collect/input`,
      name: "手动录入",
      post: async function(data) {
        return await http.post(this.url, data)
      }
    },
    result: {
      url: `/collect/result`,
      name: "获取采集结果",
      get: async function(params) {
        return await http.get(this.url, params);
      }
    },
    remove: {
      url: `/collect/delete`,
      name: "删除采集结果",
      post: async function(data) {
        return await http.post(this.url, data)
      }
    }
  }
}
