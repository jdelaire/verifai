<script setup lang="ts">
import { useRoute } from "vue-router";
import { ref, computed, onMounted, onUnmounted } from "vue";
import type { Report } from "@verifai/shared/src/types";
import { pollReport } from "../lib/polling";
import ProcessingView from "../components/ProcessingView.vue";
import ReportCard from "../components/ReportCard.vue";

const route = useRoute();
const jobId = computed(() => route.params.jobId as string);

const report = ref<Report | null>(null);
const error = ref<string | null>(null);
let cancelPoll: (() => void) | null = null;

onMounted(() => {
  cancelPoll = pollReport({
    jobId: jobId.value,
    onUpdate(r) {
      report.value = r;
    },
    onError(err) {
      error.value = err.message;
    },
  });
});

onUnmounted(() => {
  cancelPoll?.();
});

const isLoading = computed(() => {
  if (!report.value) return true;
  return report.value.status === "pending" || report.value.status === "processing";
});

const isDone = computed(() => report.value?.status === "done");
const isFailed = computed(() => report.value?.status === "failed");
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-3">
      <router-link
        to="/"
        class="text-sm text-indigo-600 hover:text-indigo-800 transition-colors"
      >
        &larr; Analyze another image
      </router-link>
    </div>

    <!-- Error state -->
    <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 p-8">
      <p class="text-red-700 font-medium">Something went wrong</p>
      <p class="mt-1 text-sm text-red-600">{{ error }}</p>
      <router-link
        to="/"
        class="mt-4 inline-block text-sm text-red-700 underline hover:text-red-900"
      >
        Try again
      </router-link>
    </div>

    <!-- Loading / processing state -->
    <ProcessingView
      v-else-if="isLoading"
      :status="(report?.status as 'pending' | 'processing') ?? 'pending'"
    />

    <!-- Failed state -->
    <div v-else-if="isFailed" class="rounded-xl border border-red-200 bg-red-50 p-8">
      <p class="text-red-700 font-medium">Analysis failed</p>
      <p class="mt-1 text-sm text-red-600">
        The image could not be analyzed. This may be due to an unsupported format or a server issue.
      </p>
      <router-link
        to="/"
        class="mt-4 inline-block text-sm text-red-700 underline hover:text-red-900"
      >
        Try again
      </router-link>
    </div>

    <!-- Done: show report -->
    <ReportCard v-else-if="isDone && report" :report="report" />
  </div>
</template>
