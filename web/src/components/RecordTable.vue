<template>
  <div class="record-table-container">
    <el-auto-resizer>
      <template #default="{ height, width }">
        <el-table-v2
          v-model:sort-state="sortState"
          :data="tableData"
          :columns="columns"
          :width="width"
          :height="height"
          fixed
          @column-sort="onSort" />
      </template>
    </el-auto-resizer>
  </div>
</template>

<script lang="ts" setup>
import { getOrderColumn } from '@/utils/tools';
import { SortBy, SortState, TableV2SortOrder } from 'element-plus';
import { h, ref, watch } from 'vue';

interface Props {
  data: any[];
  order?: string;
}

const props = defineProps<Props>();
const columns = ref<any[]>([]);
const sortState = ref<SortState>({});
const emit = defineEmits(['toAbnormal', 'toCph']);

const tableData = ref<any[]>(props.data);

const onSort = ({ key, order }: SortBy) => {
  const otherOrder =
    order === TableV2SortOrder.ASC
      ? TableV2SortOrder.DESC
      : TableV2SortOrder.ASC;
  Object.keys(sortState.value).forEach(k => {
    if (k !== key) {
      sortState.value[k] = otherOrder;
    } else {
      sortState.value[k] = order;
    }
  });
  tableData.value.sort((a, b) => {
    if (key === '地址' || key === '问券地址') {
      const aV = (a[key] || '0-0-0').split('-').map((s: string) => parseInt(s));
      const bV = (b[key] || '0-0-0').split('-').map((s: string) => parseInt(s));
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
};

// 根据数据动态生成列配置
watch(
  () => props.data,
  newData => {
    const orderColumn = getOrderColumn(props.order);
    tableData.value = newData;
    if (newData && newData.length > 0) {
      const firstRow = newData[0];
      sortState.value = {};
      Object.keys(firstRow).forEach((key: string) => {
        sortState.value[key] =
          key === orderColumn ? TableV2SortOrder.DESC : TableV2SortOrder.ASC;
      });
      columns.value = Object.keys(firstRow).map(key => ({
        key,
        dataKey: key,
        title: key,
        sortable: true,
        width: key.includes('时间') ? 180 : 120,
        cellRenderer:
          key !== '车牌号'
            ? void 0
            : ({ rowData }: { rowData: any }) =>
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
                )
      }));
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.record-table-container {
  /* height: calc(100vh - 180px); */
  flex: 1;
}

:deep(.el-table-v2) {
  --el-table-border-color: #ebeef5;
  --el-table-header-bg-color: var(--color-background-mute);
}
</style>
