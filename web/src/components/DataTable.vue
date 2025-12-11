<template>
  <div class="data-table-container">
    <el-tabs v-model="activeTab" type="card">
      <el-tab-pane
        v-for="(data, tabName) in tableData"
        :key="tabName"
        :label="tabName"
        :name="tabName">
        <div class="data-table-body">
          <div class="search-container">
            <div>
              <el-select
                v-if="hasColumn(tabName, '类型')"
                v-model="typeClassValue"
                placeholder="请选择车辆类型"
                title="车辆类型"
                style="width: 90px">
                <el-option label="全部" value="全部" />
                <el-option label="月租车" value="月租车" />
                <el-option label="亲情车" value="亲情车" />
                <el-option label="免费车" value="免费车" />
                <el-option label="临时车" value="临时车" />
              </el-select>
              <el-select
                v-if="hasColumn(tabName, '住户类型')"
                v-model="tenantValue"
                placeholder="请选择住户类型"
                title="住户类型"
                style="width: 90px">
                <el-option label="全部" value="全部" />
                <el-option label="租客" value="租客" />
                <el-option label="业主" value="业主" />
                <el-option label="未绑定" value="未绑定" />
              </el-select>
              <el-tooltip
                v-if="hasColumn(tabName, '是否参加问券')"
                content="是否参加问券"
                placement="bottom"
                effect="light">
                <el-select
                  v-model="couponValue"
                  placeholder="请选择是否参加问券"
                  style="width: 80px">
                  <el-option label="全部" value="全部" />
                  <el-option label="是" value="是" />
                  <el-option label="否" value="否" />
                </el-select>
              </el-tooltip>
              <el-tooltip
                v-if="hasColumn(tabName, '对比类型')"
                content="对比类型"
                placement="bottom"
                effect="light">
                <el-select
                  v-model="compareValue"
                  placeholder="请选择是否参加问券"
                  style="width: 90px">
                  <el-option label="全部" value="全部" />
                  <el-option label="未出现" value="未出现" />
                  <el-option label="新出现" value="新出现" />
                </el-select>
              </el-tooltip>
              <el-tooltip
                v-if="hasColumn(tabName, '最后进出时间')"
                content="最后进出时间"
                placement="bottom"
                effect="light">
                <span
                  ><el-date-picker
                    v-model="lastInOutTimeValue"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    :editable="false"
                    :shortcuts="[
                      ...dateShortcuts,
                      {
                        text: '清空',
                        value: () => [null, null]
                      }
                    ]"
                    clearable
                    style="width: 220px; flex: none"
                /></span>
              </el-tooltip>
              <el-input
                v-if="hasColumn(tabName, '车牌号')"
                v-model="plateSearchValue"
                placeholder="请输入车牌号"
                style="width: 120px"
                clearable
                @keyup.enter="handlePlateSearch" />
              <el-button
                v-if="hasColumn(tabName, '车牌号')"
                type="primary"
                @click="handlePlateSearch"
                >搜索</el-button
              >
              <el-button
                v-if="
                  hasColumn(tabName, [
                    '类型',
                    '住户类型',
                    '是否参加问券',
                    '最后进出时间',
                    '地址',
                    '车牌号'
                  ])
                "
                type="primary"
                @click="exportTableData(filteredData[tabName])"
                >导出</el-button
              >
            </div>
            <div style="text-align: right; min-width: 100px">
              共计 {{ filteredData[tabName]?.length }} 条
            </div>
          </div>
          <el-auto-resizer>
            <template #default="{ height, width }">
              <el-table-v2
                v-model:sort-state="sortState[tabName]"
                :data="filteredData[tabName]"
                :columns="columns[tabName]"
                :width="width"
                :height="height"
                fixed
                @column-sort="onSort">
              </el-table-v2>
            </template>
          </el-auto-resizer>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script lang="ts" setup>
import {
  columns_data_to_table_data,
  getOrderColumn,
  dateShortcuts
} from '@/utils/tools';
import dayjs from 'dayjs';
import {
  SortBy,
  SortState,
  TableV2FixedDir,
  TableV2SortOrder
} from 'element-plus';
import { ref, watch, reactive, computed, h } from 'vue';

interface Column {
  key: string | number;
  dataKey: string | number;
  title: string;
  width?: number;
  fixed?: boolean | TableV2FixedDir;
}

interface Props {
  tableData: Record<string, { data: any[]; columns: string[] }>;
  order?: string;
}

const emit = defineEmits(['toAbnormal', 'toCph']);
const columns = reactive({} as Record<string, Column[]>);
const props = defineProps<Props>();
const activeTab = ref(Object.keys(props.tableData)[0]);
const plateSearchValue = ref('');
const typeClassValue = ref('全部');
const tenantValue = ref('全部');
const couponValue = ref('全部');
const compareValue = ref('全部');
const lastInOutTimeValue = ref([]);
const emptyAddressValue = ref(false);
const sortState = reactive<Record<string, SortState>>({});

// 检查当前表格是否包含指定列
const hasColumn = (tabName: string, columnKey: string | string[]) => {
  if (Array.isArray(columnKey)) {
    return columnKey.some(key =>
      columns[tabName]?.some(col => col.dataKey === key)
    );
  }
  return columns[tabName]?.some(col => col.dataKey === columnKey);
};
const sortBy = reactive<
  Record<string, { key: string; order: TableV2SortOrder }>
>({});

const onSort = ({ key, order }: SortBy) => {
  sortBy[activeTab.value] = { key: key as string, order };
  if (!sortState[activeTab.value]) {
    sortState[activeTab.value] = {};
  }
  const otherOrder =
    order === TableV2SortOrder.ASC
      ? TableV2SortOrder.DESC
      : TableV2SortOrder.ASC;
  Object.keys(sortState[activeTab.value]).forEach(k => {
    if (k !== key) {
      sortState[activeTab.value][k] = otherOrder;
    } else {
      sortState[activeTab.value][k] = order;
    }
  });
};

const originalData: Record<string, any[]> = {};

// 过滤数据
const filteredData = computed(() => {
  const result: Record<string, any[]> = {};
  Object.keys(props.tableData).forEach(tabName => {
    originalData[tabName] = columns_data_to_table_data(
      props.tableData[tabName].columns,
      props.tableData[tabName].data
    );
    result[tabName] = originalData[tabName];
    if (plateSearchValue.value) {
      result[tabName] = result[tabName].filter(row => {
        const plateValue = row['车牌号'];
        return (
          plateValue &&
          plateValue
            .toLowerCase()
            .includes(plateSearchValue.value.toLowerCase())
        );
      });
    }
    if (typeClassValue.value && typeClassValue.value !== '全部') {
      result[tabName] = result[tabName].filter(
        row => row['类型'] === typeClassValue.value
      );
    }
    if (tenantValue.value && tenantValue.value !== '全部') {
      result[tabName] = result[tabName].filter(
        row => tenantValue.value === row['住户类型']
      );
    }
    if (couponValue.value && couponValue.value !== '全部') {
      result[tabName] = result[tabName].filter(
        row => couponValue.value === row['是否参加问券']
      );
    }
    if (compareValue.value && compareValue.value !== '全部') {
      result[tabName] = result[tabName].filter(
        row => compareValue.value === row['对比类型']
      );
    }
    if (
      lastInOutTimeValue.value?.length === 2 &&
      !isNaN(lastInOutTimeValue.value[0]) &&
      !isNaN(lastInOutTimeValue.value[1])
    ) {
      const start = dayjs(lastInOutTimeValue.value[0]).format(
        'YYYY-MM-DD HH:mm:ss'
      );
      const end = dayjs(lastInOutTimeValue.value[1]).format(
        'YYYY-MM-DD HH:mm:ss'
      );
      result[tabName] = originalData[tabName].filter(
        row => row['最后进出时间'] >= start && row['最后进出时间'] <= end
      );
    }
    if (emptyAddressValue.value) {
      result[tabName] = originalData[tabName].filter(row => !row['地址']);
    }
  });
  const { key, order } = sortBy[activeTab.value] || {
    key: '',
    order: TableV2SortOrder.ASC
  };
  if (!key) {
    return result;
  }
  // 创建副本进行排序，避免修改原始数据
  result[activeTab.value] = [...result[activeTab.value]].sort((a, b) => {
    if (key === '地址' || key === '问券地址') {
      const aV = (a[key] || '0-0-0').split('-').map((s: string) => parseInt(s));
      const bV = (b[key] || '0-0-0').split('-').map((s: string) => parseInt(s));
      if (order === TableV2SortOrder.ASC) {
        return aV[0] - bV[0] || aV[1] - bV[1] || aV[2] - bV[2];
      } else {
        return bV[0] - aV[0] || bV[1] - aV[1] || bV[2] - aV[2];
      }
    }
    if (key === '停车时长') {
      const aV = (a[key] || '0-0-0')
        .replace('天', '-')
        .replace('小时', '-')
        .replace('分', '-')
        .split('-')
        .map((s: string) => parseInt(s));
      const bV = (b[key] || '0-0-0')
        .replace('天', '-')
        .replace('小时', '-')
        .replace('分', '-')
        .split('-')
        .map((s: string) => parseInt(s));
      if (order === TableV2SortOrder.ASC) {
        return aV[0] - bV[0] || aV[1] - bV[1] || aV[2] - bV[2];
      } else {
        return bV[0] - aV[0] || bV[1] - aV[1] || bV[2] - aV[2];
      }
    }
    if (typeof a[key] === 'number' && typeof b[key] === 'number') {
      if (order === TableV2SortOrder.ASC) {
        return a[key] - b[key];
      } else {
        return b[key] - a[key];
      }
    }
    if (order === TableV2SortOrder.ASC) {
      return String(a[key] || '').localeCompare(String(b[key] || ''));
    } else {
      return String(b[key] || '').localeCompare(String(a[key] || ''));
    }
  });
  return result;
});

function resetColumns() {
  Object.keys(sortBy).forEach(tabName => {
    delete sortBy[tabName];
  });
  Object.keys(sortState).forEach(tabName => {
    delete sortBy[tabName];
  });
  columns[activeTab.value] = [];
  const orderColumn = getOrderColumn(props.order);
  Object.keys(props.tableData).forEach(tabName => {
    const firstRow =
      (props.tableData[tabName] && props.tableData[tabName]?.columns) || [];
    columns[tabName] = firstRow.map(m => {
      if (!sortState[tabName]) {
        sortState[tabName] = {};
      }
      sortState[tabName][m] =
        m === orderColumn ? TableV2SortOrder.DESC : TableV2SortOrder.ASC;
      return {
        key: m,
        dataKey: m,
        title: m,
        width: m?.includes('时间') ? 180 : 120,
        sortable: true,
        cellRenderer: getCellRenderer(tabName, m)
      };
    });
    columns[tabName][0].fixed = true;
    columns[tabName][1].fixed = TableV2FixedDir.LEFT;
  });
}

function getCellRenderer(tabName: string, key: string) {
  if (tabName === '异常车辆' && key === '信息') {
    return ({ rowData }: { rowData: any }) =>
      h(
        'a',
        {
          onClick: () => emit('toAbnormal', rowData['车牌号']),
          class: 'el-table-v2__cell-text',
          title: rowData['信息']
        },
        rowData['信息']
      );
  } else if (key === '车牌号') {
    return ({ rowData }: { rowData: any }) =>
      h(
        rowData['车牌号']?.length < 500 ? 'a' : 'span',
        {
          onClick:
            rowData['车牌号']?.length > 500
              ? void 0
              : () => emit('toCph', rowData['车牌号']),
          class: 'el-table-v2__cell-text',
          title: rowData['车牌号']
        },
        rowData['车牌号']
      );
  }
  return void 0;
}

// 处理车牌号搜索
const handlePlateSearch = () => {
  // 触发重新计算
  activeTab.value = activeTab.value;
};

// 初始化
watch(
  () => props.tableData,
  _ => {
    resetColumns();
    plateSearchValue.value = ''; // 重置搜索值
  },
  { immediate: true }
);

// 使用xlsx库导出表格数据
const exportTableData = (data: any[]) => {
  import('xlsx').then(XLSX => {
    const worksheet = XLSX.utils.json_to_sheet(data);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Sheet1');
    XLSX.writeFile(workbook, `${activeTab.value}_导出数据.xlsx`);
  });
};
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
  justify-content: space-between;
}

.search-container > div > * {
  margin-right: 12px;
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
:deep(.el-table-v2__left) {
  background-color: #f2f2f2;
}
</style>
