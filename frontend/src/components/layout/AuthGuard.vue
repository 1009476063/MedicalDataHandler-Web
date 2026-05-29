<template>
  <slot v-if="!authEnabled || isAuthenticated || loading" />
  <div v-else class="h-full flex items-center justify-center bg-accent-50 dark:bg-accent-950">
    <div class="text-center space-y-4">
      <ShieldCheckIcon class="w-12 h-12 text-accent-400 mx-auto" />
      <h2 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('auth.required') }}</h2>
      <p class="text-sm text-accent-500">{{ $t('auth.loginMessage') }}</p>
      <button
        class="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-sm font-medium transition-colors"
        @click="loginWithRedirect"
      >
        {{ $t('auth.login') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { ShieldCheckIcon } from '@heroicons/vue/24/outline'

const { authEnabled, isAuthenticated, loading, fetchAuthConfig, fetchUser, loginWithRedirect } = useAuth()

onMounted(async () => {
  await fetchAuthConfig()
  if (authEnabled.value) {
    await fetchUser()
  }
})
</script>
