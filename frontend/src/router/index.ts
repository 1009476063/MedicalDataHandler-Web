import { createRouter, createWebHistory } from 'vue-router'
import i18n from '@/i18n'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { titleKey: 'sidebar.nav.dashboard' },
    },
    {
      path: '/viewer',
      name: 'viewer',
      component: () => import('@/views/ViewerView.vue'),
      meta: { titleKey: 'sidebar.nav.viewer' },
    },
    {
      path: '/patients',
      name: 'patients',
      component: () => import('@/views/PatientsView.vue'),
      meta: { titleKey: 'sidebar.nav.patients' },
    },
    {
      path: '/metadata',
      name: 'metadata',
      component: () => import('@/views/MetadataView.vue'),
      meta: { titleKey: 'sidebar.nav.metadata' },
    },
    {
      path: '/data-table',
      name: 'data-table',
      component: () => import('@/views/DataTableView.vue'),
      meta: { titleKey: 'sidebar.nav.dataTable' },
    },
    {
      path: '/plans',
      name: 'plans',
      component: () => import('@/views/PlansView.vue'),
      meta: { titleKey: 'sidebar.nav.plans' },
    },
    {
      path: '/export',
      name: 'export',
      component: () => import('@/views/ExportView.vue'),
      meta: { titleKey: 'sidebar.nav.export' },
    },
    {
      path: '/processing',
      name: 'processing',
      component: () => import('@/views/PostProcessingView.vue'),
      meta: { titleKey: 'sidebar.nav.postProcessing' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { titleKey: 'sidebar.nav.settings' },
    },
  ],
})

// Preload all route chunks after initial render to eliminate navigation delay
const routeImports = [
  () => import('@/views/DashboardView.vue'),
  () => import('@/views/ViewerView.vue'),
  () => import('@/views/PatientsView.vue'),
  () => import('@/views/MetadataView.vue'),
  () => import('@/views/DataTableView.vue'),
  () => import('@/views/PlansView.vue'),
  () => import('@/views/ExportView.vue'),
  () => import('@/views/PostProcessingView.vue'),
  () => import('@/views/SettingsView.vue'),
]
const preload = () => routeImports.forEach(loader => loader())
if (typeof requestIdleCallback !== 'undefined') {
  requestIdleCallback(preload)
} else {
  setTimeout(preload, 2000)
}

router.beforeEach((to) => {
  const titleKey = to.meta.titleKey as string
  const title = titleKey ? i18n.global.t(titleKey) : 'Home'
  document.title = `${title} - MedicalDataHandler`
})

export default router
