<script setup lang="ts">
import { useRoute } from "vue-router";
import { computed } from "vue";

const route = useRoute();
const jobId = computed(() => route.params.jobId as string);
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-3">
      <router-link
        to="/"
        class="text-sm text-indigo-600 hover:text-indigo-800 transition-colors"
      >
        &larr; Back
      </router-link>
    </div>

    <section class="rounded-xl border border-gray-200 bg-white p-8">
      <div class="flex items-center gap-3">
        <div
          class="h-5 w-5 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent"
        ></div>
        <p class="text-gray-700">
          Loading report <code class="rounded bg-gray-100 px-1.5 py-0.5 text-sm font-mono">{{ jobId }}</code>&hellip;
        </p>
      </div>
    </section>
  </div>
</template>
