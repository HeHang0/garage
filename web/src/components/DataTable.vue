<template>
  <div class="data-table-container">
    <el-tabs v-model="activeTab" type="card">
      <el-tab-pane
        v-for="(data, tabName) in tableData"
        :key="tabName"
        :label="tabName"
        :name="tabName">
        <div class="data-table-body">
          <div class="search-container" v-if="hasPlateColumn(tabName)">
            <el-input
              v-model="plateSearchValue"
              placeholder="请输入车牌号"
              style="width: 200px"
              clearable
              @keyup.enter="handlePlateSearch" />
            <el-button
              type="primary"
              @click="handlePlateSearch"
              style="margin-left: 10px"
              >搜索</el-button
            >
          </div>
          <el-auto-resizer>
            <template #default="{ height, width }">
              <el-table-v2
                :data="filteredData[tabName]"
                :columns="columns[tabName]"
                :width="width"
                :height="height">
              </el-table-v2>
            </template>
          </el-auto-resizer>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, reactive, computed } from 'vue';

interface Column {
  key: string | number;
  dataKey: string | number;
  title: string;
  width?: number;
}

interface Props {
  tableData: Record<string, any[]>;
}

const columns = reactive({} as Record<string, Column[]>);
const props = defineProps<Props>();
const activeTab = ref(Object.keys(props.tableData)[0]);
const plateSearchValue = ref('');

// 检查当前表格是否包含车牌号列
const hasPlateColumn = (tabName: string) => {
  return columns[tabName]?.some(col => col.dataKey === '车牌号');
};

// 过滤数据
const filteredData = computed(() => {
  const result: Record<string, any[]> = {};
  Object.keys(props.tableData).forEach(tabName => {
    if (!plateSearchValue.value || !hasPlateColumn(tabName)) {
      result[tabName] = props.tableData[tabName];
    } else {
      result[tabName] = props.tableData[tabName].filter(row => {
        const plateValue = row['车牌号'];
        return (
          plateValue &&
          plateValue
            .toLowerCase()
            .includes(plateSearchValue.value.toLowerCase())
        );
      });
    }
  });
  return result;
});

function resetColumns() {
  Object.keys(props.tableData).forEach(tabName => {
    const firstRow =
      (props.tableData[tabName] && props.tableData[tabName][0]) || {};
    columns[tabName] = Object.keys(firstRow).map((m, i) => ({
      key: m,
      dataKey: m,
      title: m,
      width: 120
    }));
  });
}

// 处理车牌号搜索
const handlePlateSearch = () => {
  // 触发重新计算
  activeTab.value = activeTab.value;
};

// 初始化
watch(
  () => props.tableData,
  newData => {
    resetColumns();
    plateSearchValue.value = ''; // 重置搜索值
  },
  { immediate: true }
);
</script>

<style scoped>
.data-table-container {
  height: calc(100vh - 188px);
}

.data-table-body {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 245px);
}

.search-container {
  padding: 10px 0;
  display: flex;
  align-items: center;
}

:deep(.el-tabs__content) {
  padding: 20px;
  height: calc(100% - 40px);
}

:deep(.el-tab-pane) {
  height: 100%;
}

:deep(.el-table-v2) {
  --el-table-border-color: #ebeef5;
  --el-table-header-bg-color: #f5f7fa;
}
</style>
