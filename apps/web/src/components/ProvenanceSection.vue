<script setup lang="ts">
import type { Provenance } from "@verifai/shared/src/types";

defineProps<{
  provenance: Provenance;
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
            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
          />
        </svg>
        Provenance (C2PA)
      </h3>
    </div>

    <!-- Body -->
    <div class="px-5 py-4 space-y-4">
      <!-- C2PA presence -->
      <div class="flex items-center justify-between">
        <span class="text-sm text-gray-600">C2PA manifest</span>
        <span
          class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold"
          :class="provenance.c2pa_present ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-700'"
        >
          <!-- Check icon -->
          <svg
            v-if="provenance.c2pa_present"
            class="h-3.5 w-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="3"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <!-- X icon -->
          <svg
            v-else
            class="h-3.5 w-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="3"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
          {{ provenance.c2pa_present ? "Present" : "Not found" }}
        </span>
      </div>

      <!-- C2PA validation -->
      <div class="flex items-center justify-between">
        <span class="text-sm text-gray-600">Signature valid</span>
        <span
          v-if="provenance.c2pa_valid === null"
          class="inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-semibold text-gray-500"
        >
          <svg
            class="h-3.5 w-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" />
          </svg>
          N/A
        </span>
        <span
          v-else
          class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold"
          :class="provenance.c2pa_valid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-700'"
        >
          <!-- Check icon -->
          <svg
            v-if="provenance.c2pa_valid"
            class="h-3.5 w-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="3"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <!-- X icon -->
          <svg
            v-else
            class="h-3.5 w-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="3"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
          {{ provenance.c2pa_valid ? "Valid" : "Invalid" }}
        </span>
      </div>

      <!-- Divider if notes exist -->
      <div v-if="provenance.notes.length > 0" class="border-t border-gray-100 pt-3">
        <p class="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Notes</p>
        <ul class="space-y-1.5">
          <li
            v-for="(note, idx) in provenance.notes"
            :key="idx"
            class="flex items-start gap-2 text-sm text-gray-600 leading-relaxed"
          >
            <span class="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-gray-300"></span>
            <span>{{ note }}</span>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>
