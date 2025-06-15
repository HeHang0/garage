<template>
  <div class="analysis-container">
    <el-tabs
      v-model="activeTab"
      class="demo-tabs"
      tab-position="left"
      style="height: 100vh">
      <el-tab-pane label="查询" name="query">
        <div class="tab-content">
          <h2>查询</h2>
          <div class="search-container">
            <el-select
              v-model="searchType"
              placeholder="请选择搜索类型"
              style="width: 200px">
              <el-option label="车牌号" value="cph" />
              <el-option label="名称/地址" value="name" />
            </el-select>
            <el-input
              v-model="searchValue"
              :placeholder="
                searchType === 'cph'
                  ? '请输入车牌号，多个车牌号用逗号分隔'
                  : '请输入名称/地址'
              "
              style="width: 300px; margin: 0 20px" />
            <el-button type="primary" @click="handleSearch" :loading="loading"
              >搜索</el-button
            >
          </div>
          <div class="result-container" v-if="searchResult">
            <pre>{{ searchResult }}</pre>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="记录查询" name="record">
        <div class="tab-content">
          <h2>记录查询</h2>
          <div class="search-container">
            <el-input
              v-model="recordSearch.cph"
              placeholder="请输入车牌号，多个车牌号用逗号分隔"
              style="width: 300px"
              clearable />
            <el-input
              v-model="recordSearch.name"
              placeholder="请输入名称或地址"
              style="width: 200px; margin-left: 20px"
              clearable />
            <el-date-picker
              v-model="recordSearch.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :shortcuts="dateShortcuts"
              style="width: 400px; margin: 0 20px" />
            <el-button
              type="primary"
              @click="handleRecordSearch"
              :loading="loading"
              >搜索</el-button
            >
          </div>
          <RecordTable v-if="recordData" :data="recordData" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="收入汇总" name="income">
        <div class="tab-content">
          <h2>收入汇总</h2>
          <div class="button-container">
            <el-button
              type="primary"
              @click="handleDataFetch('income')"
              :loading="loading"
              >查询</el-button
            >
            <el-button type="success" @click="handleDownload('income')"
              >下载</el-button
            >
          </div>
          <DataTable v-if="tableData.income" :table-data="tableData.income" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="行为分析" name="behavior">
        <div class="tab-content">
          <h2>行为分析</h2>
          <div class="button-container">
            <el-button
              type="primary"
              @click="handleDataFetch('behavior')"
              :loading="loading"
              >查询</el-button
            >
            <el-button type="success" @click="handleDownload('behavior')"
              >下载</el-button
            >
          </div>
          <DataTable
            v-if="tableData.behavior"
            :table-data="tableData.behavior" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="车牌分析" name="plate">
        <div class="tab-content">
          <h2>车牌分析</h2>
          <div class="button-container">
            <el-button
              type="primary"
              @click="handleDataFetch('plate')"
              :loading="loading"
              >查询</el-button
            >
            <el-button type="success" @click="handleDownload('plate')"
              >下载</el-button
            >
          </div>
          <DataTable v-if="tableData.plate" :table-data="tableData.plate" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref } from 'vue';
import request from '../utils/request';
import { ElMessage } from 'element-plus';
import DataTable from './DataTable.vue';
import RecordTable from './RecordTable.vue';
import dayjs from 'dayjs';

const activeTab = ref('query');
const searchType = ref('cph');
const searchValue = ref('');
const searchResult = ref('');
const loading = ref(false);
const recordData = ref<any[]>([]);

// 记录查询相关
const recordSearch = reactive({
  cph: '',
  name: '',
  dateRange: [dayjs().subtract(1, 'month').toDate(), dayjs().toDate()]
});

// 日期快捷选项
const dateShortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
      return [start, end];
    }
  },
  {
    text: '最近一个月',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
      return [start, end];
    }
  },
  {
    text: '最近三个月',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
      return [start, end];
    }
  },
  {
    text: '最近一年',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 365);
      return [start, end];
    }
  },
  {
    text: '最近两年',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 365 * 2);
      return [start, end];
    }
  }
];

// 表格数据
const tableData = reactive<Record<string, any>>({
  income: null,
  behavior: null,
  plate: null
});

// 记录查询处理
const handleRecordSearch = async () => {
  if (!recordSearch.cph && !recordSearch.name) {
    ElMessage.warning('请输入车牌号或名称');
    return;
  }

  if (!recordSearch.dateRange || recordSearch.dateRange.length !== 2) {
    ElMessage.warning('请选择日期范围');
    return;
  }

  loading.value = true;
  try {
    const [start, end] = recordSearch.dateRange;
    const response = await request.get('/api/record', {
      params: {
        cph: recordSearch.cph || '',
        name: recordSearch.name || '',
        start: dayjs(start).format('YYYY-MM-DD'),
        end: dayjs(end).format('YYYY-MM-DD')
      }
    });
    recordData.value = Array.isArray(response) ? response : [response];
  } catch (error) {
    console.error('获取记录失败:', error);
  } finally {
    loading.value = false;
  }
};

// 查询处理
const handleSearch = async () => {
  if (!searchValue.value) {
    ElMessage.warning('请输入搜索内容');
    return;
  }

  loading.value = true;
  try {
    const url = searchType.value === 'cph' ? '/api/cph' : '/api/name';
    const param = searchType.value === 'cph' ? 'cph' : 'name';
    const response = await request.get(url, {
      params: {
        [param]: searchValue.value
      }
    });
    searchResult.value = response as any;
  } catch (error) {
    console.error('搜索失败:', error);
  } finally {
    loading.value = false;
  }
};

// 数据获取处理
const handleDataFetch = async (type: 'income' | 'behavior' | 'plate') => {
  loading.value = true;
  try {
    const url = `/api/${type === 'plate' ? 'area' : type}`;
    const response = await request.get(url);
    console.log('得到的数据', response);
    tableData[type] = response;
  } catch (error) {
    console.error('获取数据失败:', error);
  } finally {
    loading.value = false;
  }
  console.log('啦啦啦', tableData);
};

// 下载处理
const handleDownload = (type: 'income' | 'behavior' | 'plate') => {
  window.open(
    `${
      import.meta.env.DEV ? 'http://localhost:8080' : window.location.origin
    }/api/${type === 'plate' ? 'area' : type}/excel`
  );
};
</script>

<style scoped>
.analysis-container {
  width: 100%;
  height: 100vh;
  background-color: #f5f7fa;
}

.tab-content {
  padding: 20px;
  background-color: #fff;
  border-radius: 4px;
  min-height: calc(100vh - 40px);
  margin: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  width: calc(100% - 40px);
}

.search-container {
  margin: 20px 0;
  display: flex;
  align-items: center;
}

.button-container {
  margin: 20px 0;
  display: flex;
  gap: 10px;
}

.result-container {
  margin-top: 20px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 4px;
  white-space: pre-wrap;
  font-family: monospace;
  width: 100%;
  min-height: 200px;
}
.result-container > pre {
  white-space: pre-wrap;
}

:deep(.el-tabs__content) {
  height: 100%;
  overflow: auto;
}

:deep(.el-tabs__item) {
  height: 50px;
  line-height: 50px;
  font-size: 16px;
}

:deep(.el-tabs__item.is-active) {
  color: #409eff;
  font-weight: bold;
}

:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #e4e7ed;
}

:deep(.el-tabs__content) {
  padding: 0;
}

:deep(.el-tab-pane) {
  height: calc(100% - 20px);
}
</style>
