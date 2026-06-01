import { createRouter, createWebHistory } from 'vue-router'

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
      path: '/worklist',
      name: 'worklist',
      component: () => import('@/views/WorklistView.vue'),
      meta: { titleKey: 'sidebar.nav.worklist' },
    },
    {
      path: '/analysis',
      name: 'analysis',
      component: () => import('@/views/AnalysisView.vue'),
      meta: { titleKey: 'sidebar.nav.analysis' },
    },
    {
      path: '/sr',
      name: 'sr',
      component: () => import('@/views/SRView.vue'),
      meta: { titleKey: 'sidebar.nav.sr' },
    },
    {
      path: '/logging',
      name: 'logging',
      component: () => import('@/views/LoggingView.vue'),
      meta: { titleKey: 'sidebar.nav.logging' },
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

// Cache i18n module — avoid re-importing on every navigation
let _i18n: any = null
async function getI18n() {
  if (!_i18n) {
    const mod = await import('@/i18n')
    _i18n = mod.default
  }
  return _i18n
}

router.beforeEach(async (to) => {
  const titleKey = to.meta.titleKey as string
  if (titleKey) {
    try {
      const i18n = await getI18n()
      document.title = `${i18n.global.t(titleKey)} - MedVista`
    } catch {
      document.title = 'MedVista'
    }
  } else {
    document.title = 'MedVista'
  }

  // Auth guard: skip for login/callback routes
  const publicRoutes = ['login', 'auth-callback']
  if (publicRoutes.includes(to.name as string)) return

  // Await auth check — ensures we know the answer before deciding
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

export default router
