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
              style="width: 300px" />
            <el-button type="primary" @click="handleSearch" :loading="loading"
              >搜索</el-button
            >
          </div>
          <div class="result-container" v-if="searchResult">
            <pre v-html="searchResult"></pre>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="记录查询" name="record">
        <div class="tab-content">
          <h2>记录查询</h2>
          <div class="search-container">
            <el-select
              v-model="recordSearchType"
              placeholder="请选择搜索类型"
              style="width: 120px">
              <el-option label="车牌号" value="cph" />
              <el-option label="名称/地址" value="name" />
            </el-select>
            <el-input
              v-model="recordSearchValue"
              :placeholder="
                recordSearchType === 'cph'
                  ? '请输入车牌号，多个车牌号用逗号分隔'
                  : '请输入名称/地址'
              "
              style="width: 300px"
              clearable />
            <el-select
              v-model="dateType"
              placeholder="请选择日期类型"
              style="width: 120px">
              <el-option label="日期区间" value="range" />
              <el-option label="日期" value="single" />
              <el-option label="异常进出" value="abnormal" />
            </el-select>
            <el-date-picker
              v-if="dateType === 'range'"
              v-model="recordSearch.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :shortcuts="dateShortcuts"
              style="width: 300px; flex: none" />
            <el-date-picker
              v-if="dateType === 'single'"
              v-model="recordSearch.singleDate"
              type="date"
              placeholder="请选择日期"
              style="width: 180px" />
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
            :table-data="tableData.behavior"
            @toAbnormal="handleToAbnormal" />
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
import { columns_data_to_table_data } from '@/utils/tools';

const activeTab = ref('query');
const searchType = ref('cph');
const searchValue = ref('');
const searchResult = ref('');
const loading = ref(false);
const recordData = ref<any[]>([]);

// 记录查询相关
const recordSearchType = ref('cph');
const recordSearchValue = ref('');
const dateType = ref('range');
const recordSearch = reactive({
  cph: '',
  name: '',
  dateRange: [dayjs().subtract(1, 'month').toDate(), dayjs().toDate()],
  singleDate: dayjs().toDate()
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
  },
  {
    text: '最近三年',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 365 * 3);
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

const handleToAbnormal = (plate: string) => {
  recordSearchType.value = 'cph';
  recordSearchValue.value = plate;
  dateType.value = 'abnormal';
  activeTab.value = 'record';
  handleRecordSearch();
};

const handleToPlateDate = (e: Event) => {
  const target = e.target as HTMLAnchorElement;
  const { cph, date } = target?.dataset as { cph: string; date: string };
  if (!cph || !date) {
    return;
  }
  recordSearchType.value = 'cph';
  recordSearchValue.value = cph;
  dateType.value = 'single';
  activeTab.value = 'record';
  recordSearch.singleDate = dayjs(date).toDate();
  handleRecordSearch();
};
(window as any).toPlateDate = handleToPlateDate;

// 记录查询处理
const handleRecordSearch = async () => {
  // 搜索内容赋值
  recordSearch.cph =
    recordSearchType.value === 'cph' ? recordSearchValue.value : '';
  recordSearch.name =
    recordSearchType.value === 'name' ? recordSearchValue.value : '';

  if (!recordSearch.cph && !recordSearch.name) {
    ElMessage.warning('请输入车牌号或名称');
    return;
  }

  // 日期类型判断
  let params: any = {
    cph: recordSearch.cph || '',
    name: recordSearch.name || ''
  };

  if (dateType.value === 'range') {
    if (!recordSearch.dateRange || recordSearch.dateRange.length !== 2) {
      ElMessage.warning('请选择日期范围');
      return;
    }
    const [start, end] = recordSearch.dateRange;
    params.start = dayjs(start).format('YYYY-MM-DD');
    params.end = dayjs(end).format('YYYY-MM-DD');
  } else if (dateType.value === 'single') {
    if (!recordSearch.singleDate) {
      ElMessage.warning('请选择日期');
      return;
    }
    params.date = dayjs(recordSearch.singleDate).format('YYYY-MM-DD');
  } else if (dateType.value === 'abnormal') {
    params.abnormal = true;
  }

  loading.value = true;
  try {
    const response: any = await request.get('/api/record', { params });
    recordData.value = columns_data_to_table_data(
      response.columns,
      response.data
    );
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
    tableData[type] = response;
  } catch (error) {
    console.error('获取数据失败:', error);
  } finally {
    loading.value = false;
  }
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
  background-color: var(--color-background);
  --el-text-color-primary: var(--color-text);
  --el-text-color-regular: var(--color-text);
}

:deep(a) {
  cursor: pointer;
}

.tab-content {
  padding: 20px;
  background-color: var(--color-background-soft);
  border-radius: 4px;
  min-height: calc(100vh - 40px);
  margin: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  width: calc(100% - 40px);
}

.search-container {
  margin: 20px 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
}

.button-container {
  margin: 20px 0;
  display: flex;
  gap: 10px;
}

.result-container {
  margin-top: 20px;
  padding: 20px;
  background-color: var(--color-background-mute);
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
  /* color: #409eff; */
  font-weight: bold;
}

:deep(.el-tabs--card > .el-tabs__header .el-tabs__item.is-active) {
  border-bottom-color: var(--color-background-soft);
}

:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: var(--color-border);
}

:deep(.el-tabs--card > .el-tabs__header .el-tabs__item),
:deep(.el-tabs--card > .el-tabs__header .el-tabs__nav) {
  border-bottom-color: var(--color-background-soft);
  height: var(--el-tabs-header-height);
}

:deep(.el-input__wrapper) {
  background-color: var(--color-background-mute);
}

:deep(.el-select__wrapper) {
  background-color: var(--color-background-mute);
}

:deep(.el-tabs__content) {
  padding: 0;
}

:deep(.el-tab-pane) {
  height: calc(100% - 20px);
}

:deep(.el-table-v2__main) {
  background-color: var(--color-background-mute);
  border-radius: 4px;
}

:deep(.el-table-v2__header-row) {
  border-bottom: 1px solid var(--color-border);
}
:deep(.el-table-v2__row:hover) {
  background-color: var(--color-border-hover) !important;
}
:deep(.el-table-v2__row) {
  border-color: var(--color-border) !important;
}
:deep(.el-table-v2__header-cell) {
  background-color: transparent !important;
}
</style>
<style>
.el-popper__arrow:before,
.el-select__popper.el-popper {
  background-color: var(--color-background-mute) !important;
}
.el-select-dropdown__item.is-selected {
  background-color: var(--color-border-hover);
}
.el-select-dropdown__item.is-hovering {
  background-color: var(--color-border);
}
</style>
