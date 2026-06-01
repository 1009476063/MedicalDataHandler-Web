<template>
  <div class="space-y-1">
    <div
      v-for="node in nodes"
      :key="node.id"
      class="rounded-lg border border-accent-200 dark:border-accent-700 overflow-hidden"
    >
      <button
        class="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-accent-50 dark:hover:bg-accent-700/50 transition-colors"
        @click="toggle(node.id)"
      >
        <ChevronRightIcon
          v-if="node.children.length"
          :class="['w-4 h-4 text-accent-400 transition-transform', expanded[node.id] && 'rotate-90']"
        />
        <span v-else class="w-4" />
        <span class="text-xs font-medium text-accent-700 dark:text-accent-300">
          {{ node.concept_name }}
        </span>
        <span
          v-if="node.value"
          class="text-xs text-accent-500 dark:text-accent-400 ml-auto truncate max-w-[200px]"
        >
          {{ node.value }}
        </span>
      </button>
      <div v-if="expanded[node.id] && node.children.length" class="px-3 pb-2">
        <SRContentTree :nodes="node.children" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import type { ContentTreeNode } from '@/types'
import { ChevronRightIcon } from '@heroicons/vue/24/outline'

defineProps<{ nodes: ContentTreeNode[] }>()

const expanded = reactive<Record<string, boolean>>({})

function toggle(id: string) {
  expanded[id] = !expanded[id]
}
</script>
