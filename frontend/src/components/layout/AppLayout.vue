<template>
  <div class="min-h-screen">
    <AppSidebar
      :collapsed="sidebarCollapsed"
      :mobile-open="mobileMenuOpen"
      @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
      @toggle-mobile="mobileMenuOpen = !mobileMenuOpen"
    />

    <div
      :class="[
        'flex flex-col min-h-screen transition-all duration-300',
        sidebarCollapsed ? 'lg:ml-[72px]' : 'lg:ml-[256px]'
      ]"
    >
      <AppHeader
        :sidebar-collapsed="sidebarCollapsed"
        @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed"
        @toggle-mobile="mobileMenuOpen = !mobileMenuOpen"
      />

      <main class="flex-1 p-4 lg:p-6 min-h-0">
        <slot />
      </main>
    </div>

    <Transition name="fade">
      <div
        v-if="mobileMenuOpen"
        class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
        @click="mobileMenuOpen = false"
      />
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
import { useSettings } from '@/composables/useSettings'

const { sidebarCollapsed } = useSettings()
const mobileMenuOpen = ref(false)
</script>
