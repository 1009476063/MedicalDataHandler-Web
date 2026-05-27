<template>
  <router-link
    :to="item.path"
    :class="[
      'flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group',
      isActive
        ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
        : 'text-accent-600 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-800'
    ]"
  >
    <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
    <Transition name="fade">
      <span v-if="!collapsed" class="text-sm font-medium truncate">{{ item.label }}</span>
    </Transition>
  </router-link>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

interface NavItem {
  path: string
  label: string
  icon: any
}

const props = defineProps<{
  item: NavItem
  collapsed: boolean
}>()

const route = useRoute()
const isActive = computed(() => {
  if (props.item.path === '/') return route.path === '/'
  return route.path.startsWith(props.item.path)
})
</script>
