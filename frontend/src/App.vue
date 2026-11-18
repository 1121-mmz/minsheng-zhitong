<template>
  <router-view />
</template>

<style>
/* 暴力清除所有默认边距和滚动条 */
html, body, #app {
  margin: 0 !important;
  padding: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  overflow: hidden !important;
}
</style>