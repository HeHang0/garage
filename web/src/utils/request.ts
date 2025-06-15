import axios, { AxiosResponse, AxiosError } from 'axios';
import { ElMessage } from 'element-plus';

interface ApiResponse {
  data: string;
}

const baseURL = import.meta.env.DEV
  ? 'http://localhost:8080'
  : window.location.origin;

const request = axios.create({
  baseURL,
  timeout: 600000
});

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    if (
      response.headers['content-type']?.includes('json') &&
      typeof response.data === 'string'
    ) {
      const data = JSON.parse(response.data);
      return data.data;
    }
    return response.data.data;
  },
  (error: AxiosError) => {
    ElMessage.error(error.message || '请求失败');
    return Promise.reject(error);
  }
);

export default request;
