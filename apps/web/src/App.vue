<script setup lang="ts">
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900">
    <header class="border-b border-gray-200 bg-white">
      <div class="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <router-link to="/" class="text-xl font-bold tracking-tight text-indigo-600">
          VerifAI
        </router-link>
        <nav class="flex items-center gap-4 text-sm text-gray-500">
          <router-link to="/" class="hover:text-gray-900 transition-colors">
            Home
          </router-link>
        </nav>
      </div>
    </header>

    <main class="mx-auto max-w-5xl px-6 py-10">
      <router-view />
    </main>

    <footer class="border-t border-gray-200 bg-white">
      <div class="mx-auto max-w-5xl px-6 py-4 text-center text-xs text-gray-400">
        VerifAI &mdash; AI-powered document verification
      </div>
    </footer>
  </div>
</template>
