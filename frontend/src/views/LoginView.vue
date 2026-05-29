<template>
  <div class="h-full flex items-center justify-center bg-accent-50 dark:bg-accent-950 animate-fade-in">
    <div class="w-full max-w-sm mx-4">
      <div class="bg-white dark:bg-accent-900 rounded-2xl shadow-lg border border-accent-200 dark:border-accent-700 p-8 space-y-6">
        <div class="text-center space-y-2">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center mx-auto">
            <span class="text-white font-bold text-lg">M</span>
          </div>
          <h1 class="text-xl font-semibold text-accent-900 dark:text-white">{{ $t('auth.title') }}</h1>
          <p class="text-sm text-accent-500">{{ $t('auth.subtitle') }}</p>
        </div>

        <div v-if="authEnabled" class="space-y-3">
          <button
            class="w-full px-4 py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
            :disabled="loading"
            @click="loginWithRedirect"
          >
            <ArrowRightOnRectangleIcon class="w-4 h-4" />
            {{ $t('auth.loginOidc') }}
          </button>
        </div>

        <div v-else class="space-y-3">
          <button
            class="w-full px-4 py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
            :disabled="loading"
            @click="loginLocally"
          >
            <ArrowRightOnRectangleIcon class="w-4 h-4" />
            {{ $t('auth.loginLocal') }}
          </button>
          <p class="text-xs text-center text-accent-400">{{ $t('auth.noOidc') }}</p>
        </div>

        <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p class="text-xs text-red-600 dark:text-red-400">{{ error }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { ArrowRightOnRectangleIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const router = useRouter()
const { authEnabled, loading, fetchAuthConfig, fetchUser, handleCallback, loginLocally, loginWithRedirect, isAuthenticated } = useAuth()

const error = ref('')

onMounted(async () => {
  await fetchAuthConfig()

  // Handle OIDC callback
  const code = route.query.code as string
  if (code) {
    try {
      await handleCallback(code)
    } catch {
      error.value = 'Authentication failed. Please try again.'
    }
    return
  }

  // Already authenticated — redirect to home
  if (isAuthenticated.value) {
    router.push('/')
  }
})
</script>
