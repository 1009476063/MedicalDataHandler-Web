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
      path: '/converter',
      name: 'converter',
      component: () => import('@/views/ConverterView.vue'),
      meta: { titleKey: 'sidebar.nav.converter' },
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
    {
      path: '/pacs',
      name: 'pacs',
      component: () => import('@/views/PacsView.vue'),
      meta: { titleKey: 'sidebar.nav.pacs' },
    },
    {
      path: '/anonymization',
      name: 'anonymization',
      component: () => import('@/views/AnonymizationView.vue'),
      meta: { titleKey: 'sidebar.nav.anonymization' },
    },
    {
      path: '/offline',
      name: 'offline',
      component: () => import('@/views/OfflineViewerView.vue'),
      meta: { titleKey: 'sidebar.nav.offline' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { titleKey: 'auth.title' },
    },
    {
      path: '/auth/callback',
      name: 'auth-callback',
      component: () => import('@/views/LoginView.vue'),
      meta: { titleKey: 'auth.title' },
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
  () => import('@/views/ConverterView.vue'),
  () => import('@/views/PostProcessingView.vue'),
  () => import('@/views/SettingsView.vue'),
  () => import('@/views/PacsView.vue'),
  () => import('@/views/AnonymizationView.vue'),
  () => import('@/views/OfflineViewerView.vue'),
  () => import('@/views/LoginView.vue'),
]
const preload = () => routeImports.forEach(loader => loader())
if (typeof requestIdleCallback !== 'undefined') {
  requestIdleCallback(preload)
} else {
  setTimeout(preload, 2000)
}

router.beforeEach(async (to) => {
  const titleKey = to.meta.titleKey as string
  const title = titleKey ? i18n.global.t(titleKey) : 'Home'
  document.title = `${title} - MedVista`

  // Auth guard: skip for login/callback routes
  const publicRoutes = ['login', 'auth-callback']
  if (publicRoutes.includes(to.name as string)) return

  // Wait for auth config check to complete on first navigation
  await checkAuthEnabled()

  const token = localStorage.getItem('mdh_access_token')
  if (!token && authCheckEnabled) {
    return { name: 'login' }
  }
})

// Auth check cache — fetch once, then use cached result
let authCheckEnabled = false
let authChecked = false
let authCheckPromise: Promise<void> | null = null
function checkAuthEnabled() {
  if (authChecked) return Promise.resolve()
  if (authCheckPromise) return authCheckPromise
  authCheckPromise = (async () => {
    try {
      const resp = await fetch('/api/auth/config')
      const config = await resp.json()
      authCheckEnabled = config.enabled === true
    } catch {
      authCheckEnabled = false
    }
    authChecked = true
  })()
  return authCheckPromise
}
checkAuthEnabled()

export default router
