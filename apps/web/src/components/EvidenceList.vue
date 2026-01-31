<script setup lang="ts">
defineProps<{
  items: string[];
}>();
</script>

<template>
  <section class="rounded-xl border border-gray-200 bg-white overflow-hidden">
    <!-- Header -->
    <div class="border-b border-gray-100 bg-gray-50/60 px-5 py-3">
      <h3 class="flex items-center gap-2 text-sm font-semibold text-gray-800">
        <svg
          class="h-4 w-4 text-indigo-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        Evidence
      </h3>
    </div>

    <!-- Body -->
    <div class="px-5 py-4">
      <ul v-if="items.length > 0" class="space-y-3">
        <li
          v-for="(item, idx) in items"
          :key="idx"
          class="flex items-start gap-3 text-sm text-gray-700 leading-relaxed"
        >
          <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-400"></span>
          <span>{{ item }}</span>
        </li>
      </ul>
      <p v-else class="text-sm text-gray-400 italic">
        No evidence items available.
      </p>
    </div>
  </section>
</template>
