<template>
  <div class="record-table-container">
    <el-auto-resizer>
      <template #default="{ height, width }">
        <el-table-v2
          :data="data"
          :columns="columns"
          :width="width"
          :height="height" />
      </template>
    </el-auto-resizer>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';

interface Props {
  data: any[];
}

const props = defineProps<Props>();
const columns = ref<any[]>([]);

// 根据数据动态生成列配置
watch(
  () => props.data,
  newData => {
    if (newData && newData.length > 0) {
      const firstRow = newData[0];
      columns.value = Object.keys(firstRow).map(key => ({
        key,
        dataKey: key,
        title: key,
        width: key.includes('时间') ? 180 : 120
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
