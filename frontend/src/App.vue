<template>
  <div class="min-h-screen bg-accent-50 dark:bg-accent-950">
    <div class="mesh-gradient" />
    <AppLayout>
      <RouterView v-slot="{ Component }">
        <component :is="Component" />
      </RouterView>
    </AppLayout>
  </div>
</template>

<script setup lang="ts">
import AppLayout from './components/layout/AppLayout.vue'
import { RouterView } from 'vue-router'
</script>
