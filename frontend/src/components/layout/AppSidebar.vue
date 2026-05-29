<template>
  <aside
    :class="[
      'fixed top-0 left-0 z-50 h-full bg-white dark:bg-accent-900 border-r border-accent-200 dark:border-accent-700 transition-all duration-300 flex flex-col',
      'hidden lg:flex',
      collapsed ? 'w-[72px]' : 'w-[256px]',
    ]"
  >
    <div class="flex items-center gap-3 px-4 py-5 border-b border-accent-200 dark:border-accent-700">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center flex-shrink-0">
        <span class="text-white font-bold text-sm">M</span>
      </div>
      <Transition name="fade">
        <div v-if="!collapsed" class="flex-1 min-w-0">
          <h1 class="text-sm font-semibold text-accent-900 dark:text-white truncate">{{ $t('sidebar.brand') }}</h1>
          <p class="text-xs text-accent-500">{{ $t('sidebar.version') }}</p>
        </div>
      </Transition>
    </div>

    <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-6">
      <div>
        <p v-if="!collapsed" class="px-3 mb-2 text-xs font-medium text-accent-400 uppercase tracking-wider">
          {{ $t('sidebar.dataSection') }}
        </p>
        <div class="space-y-1">
          <SidebarLink
            v-for="item in dataNavItems"
            :key="item.path"
            :item="item"
            :collapsed="collapsed"
          />
        </div>
      </div>

      <div>
        <p v-if="!collapsed" class="px-3 mb-2 text-xs font-medium text-accent-400 uppercase tracking-wider">
          {{ $t('sidebar.toolsSection') }}
        </p>
        <div class="space-y-1">
          <SidebarLink
            v-for="item in toolNavItems"
            :key="item.path"
            :item="item"
            :collapsed="collapsed"
          />
        </div>
      </div>
    </nav>

    <div class="border-t border-accent-200 dark:border-accent-700 p-3 space-y-2">
      <button
        @click="toggleTheme"
        class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-accent-600 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-800 transition-colors"
      >
        <SunIcon v-if="isDark" class="w-5 h-5 flex-shrink-0" />
        <MoonIcon v-else class="w-5 h-5 flex-shrink-0" />
        <Transition name="fade">
          <span v-if="!collapsed" class="text-sm">{{ isDark ? $t('sidebar.lightMode') : $t('sidebar.darkMode') }}</span>
        </Transition>
      </button>

      <button
        @click="$emit('toggle-collapse')"
        class="hidden lg:flex w-full items-center gap-3 px-3 py-2 rounded-xl text-accent-600 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-800 transition-colors"
      >
        <ChevronLeftIcon
          :class="['w-5 h-5 flex-shrink-0 transition-transform', collapsed && 'rotate-180']"
        />
        <Transition name="fade">
          <span v-if="!collapsed" class="text-sm">{{ $t('sidebar.collapse') }}</span>
        </Transition>
      </button>
    </div>
  </aside>

  <Transition name="slide-in-right">
    <aside
      v-if="mobileOpen"
      class="fixed top-0 left-0 z-50 h-full w-[280px] bg-white dark:bg-accent-900 border-r border-accent-200 dark:border-accent-700 flex flex-col lg:hidden"
    >
      <div class="flex items-center gap-3 px-4 py-5 border-b border-accent-200 dark:border-accent-700">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center flex-shrink-0">
          <span class="text-white font-bold text-sm">M</span>
        </div>
        <div class="flex-1 min-w-0">
          <h1 class="text-sm font-semibold text-accent-900 dark:text-white truncate">{{ $t('sidebar.brand') }}</h1>
          <p class="text-xs text-accent-500">{{ $t('sidebar.version') }}</p>
        </div>
      </div>

      <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-6">
        <div>
          <p class="px-3 mb-2 text-xs font-medium text-accent-400 uppercase tracking-wider">{{ $t('sidebar.dataSection') }}</p>
          <div class="space-y-1">
            <SidebarLink
              v-for="item in dataNavItems"
              :key="item.path"
              :item="item"
              :collapsed="false"
            />
          </div>
        </div>
        <div>
          <p class="px-3 mb-2 text-xs font-medium text-accent-400 uppercase tracking-wider">{{ $t('sidebar.toolsSection') }}</p>
          <div class="space-y-1">
            <SidebarLink
              v-for="item in toolNavItems"
              :key="item.path"
              :item="item"
              :collapsed="false"
            />
          </div>
        </div>
      </nav>

      <div class="border-t border-accent-200 dark:border-accent-700 p-3">
        <button
          @click="toggleTheme"
          class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-accent-600 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-800 transition-colors"
        >
          <SunIcon v-if="isDark" class="w-5 h-5" />
          <MoonIcon v-else class="w-5 h-5" />
          <span class="text-sm">{{ isDark ? $t('sidebar.lightMode') : $t('sidebar.darkMode') }}</span>
        </button>
      </div>
    </aside>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTheme } from '@/composables/useTheme'
import SidebarLink from './SidebarLink.vue'
import {
  SunIcon, MoonIcon, ChevronLeftIcon,
  HomeIcon, UserGroupIcon, CubeTransparentIcon,
  ArrowUpTrayIcon, CogIcon, DocumentTextIcon,
  BeakerIcon, TableCellsIcon, WrenchScrewdriverIcon,
  ArrowsRightLeftIcon, GlobeAltIcon, ShieldCheckIcon,
  WifiIcon
} from '@heroicons/vue/24/outline'

interface Props {
  collapsed: boolean
  mobileOpen: boolean
}

defineProps<Props>()
defineEmits<{
  'toggle-collapse': []
  'toggle-mobile': []
}>()

const { isDark, toggle: toggleTheme } = useTheme()
const { t } = useI18n()

const dataNavItems = computed(() => [
  { path: '/', label: t('sidebar.nav.dashboard'), icon: HomeIcon },
  { path: '/patients', label: t('sidebar.nav.patients'), icon: UserGroupIcon },
  { path: '/viewer', label: t('sidebar.nav.viewer'), icon: CubeTransparentIcon },
  { path: '/data-table', label: t('sidebar.nav.dataTable'), icon: TableCellsIcon },
  { path: '/plans', label: t('sidebar.nav.plans'), icon: BeakerIcon },
  { path: '/pacs', label: t('sidebar.nav.pacs'), icon: GlobeAltIcon },
])

const toolNavItems = computed(() => [
  { path: '/converter', label: t('sidebar.nav.converter'), icon: ArrowsRightLeftIcon },
  { path: '/metadata', label: t('sidebar.nav.metadata'), icon: DocumentTextIcon },
  { path: '/processing', label: t('sidebar.nav.postProcessing'), icon: WrenchScrewdriverIcon },
  { path: '/export', label: t('sidebar.nav.export'), icon: ArrowUpTrayIcon },
  { path: '/anonymization', label: t('sidebar.nav.anonymization'), icon: ShieldCheckIcon },
  { path: '/offline', label: t('sidebar.nav.offline'), icon: WifiIcon },
  { path: '/settings', label: t('sidebar.nav.settings'), icon: CogIcon },
])
</script>
