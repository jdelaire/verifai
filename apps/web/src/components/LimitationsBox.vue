<script setup lang="ts">
defineProps<{
  items: string[];
}>();
</script>

<template>
  <section class="rounded-xl border border-amber-200 bg-amber-50 overflow-hidden">
    <!-- Header -->
    <div class="border-b border-amber-200 bg-amber-100/60 px-5 py-3">
      <h3 class="flex items-center gap-2 text-sm font-semibold text-amber-800">
        <svg
          class="h-4 w-4 text-amber-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        Limitations
      </h3>
    </div>

    <!-- Body -->
    <div class="px-5 py-4">
      <ul v-if="items.length > 0" class="space-y-2.5">
        <li
          v-for="(item, idx) in items"
          :key="idx"
          class="flex items-start gap-3 text-sm text-amber-900 leading-relaxed"
        >
          <svg
            class="mt-0.5 h-4 w-4 shrink-0 text-amber-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 9v2m0 4h.01"
            />
          </svg>
          <span>{{ item }}</span>
        </li>
      </ul>
      <p v-else class="text-sm text-amber-700 italic">
        No specific limitations noted.
      </p>
    </div>
  </section>
</template>
