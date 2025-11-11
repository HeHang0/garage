<script lang="ts" setup>
import zhCn from 'element-plus/es/locale/lang/zh-cn';
import DataAnalysis from './components/DataAnalysis.vue';
</script>

<template>
  <el-config-provider :locale="zhCn">
    <DataAnalysis />
  </el-config-provider>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    'Helvetica Neue', Arial, sans-serif;
}
</style>
