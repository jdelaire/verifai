<script setup lang="ts">
import { computed, ref } from "vue";
import type { Report } from "@verifai/shared/src/types";
import ScoreGauge from "./ScoreGauge.vue";
import EvidenceList from "./EvidenceList.vue";
import ProvenanceSection from "./ProvenanceSection.vue";
import MetadataSection from "./MetadataSection.vue";
import LimitationsBox from "./LimitationsBox.vue";

const props = defineProps<{
  report: Report;
}>();

const expiresFormatted = computed(() => {
  try {
    return new Date(props.report.expires_at).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return props.report.expires_at;
  }
});

const shareUrl = computed(() => {
  return `${window.location.origin}/report/${props.report.job_id}`;
});

const copied = ref(false);

async function copyShareLink() {
  try {
    await navigator.clipboard.writeText(shareUrl.value);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch {
    // Clipboard API may fail in some contexts; silently degrade
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Verdict + Score header -->
    <section class="rounded-xl border border-gray-200 bg-white p-6 sm:p-8">
      <div
        v-if="report.ai_likelihood !== null && report.confidence !== null"
        class="flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:gap-10"
      >
        <!-- Score gauge -->
        <div class="shrink-0">
          <ScoreGauge
            :score="report.ai_likelihood"
            :confidence="report.confidence"
          />
        </div>

        <!-- Verdict text -->
        <div class="flex-1 text-center sm:text-left">
          <h2 class="text-2xl font-bold text-gray-900 leading-tight">
            AI Likelihood: {{ report.ai_likelihood }}%
          </h2>
          <p
            v-if="report.verdict_text"
            class="mt-3 text-base text-gray-600 leading-relaxed"
          >
            {{ report.verdict_text }}
          </p>
          <div class="mt-4 flex items-center gap-2 text-xs text-gray-400 sm:justify-start justify-center">
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
            </svg>
            <code class="font-mono">{{ report.job_id }}</code>
          </div>
        </div>
      </div>

      <!-- ML unavailable fallback -->
      <div v-else class="text-center py-4">
        <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gray-100">
          <svg
            class="h-7 w-7 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <h2 class="text-xl font-bold text-gray-900">
          ML analysis unavailable
        </h2>
        <p class="mt-2 text-sm text-gray-500 max-w-md mx-auto">
          The AI detection model could not produce a score for this image.
          The report still includes metadata and provenance information below.
        </p>
        <p
          v-if="report.verdict_text"
          class="mt-4 text-base text-gray-600 leading-relaxed"
        >
          {{ report.verdict_text }}
        </p>
        <div class="mt-4 flex items-center justify-center gap-2 text-xs text-gray-400">
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
          </svg>
          <code class="font-mono">{{ report.job_id }}</code>
        </div>
      </div>
    </section>

    <!-- Evidence + Provenance two-column grid -->
    <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
      <EvidenceList :items="report.evidence" />
      <ProvenanceSection :provenance="report.provenance" />
    </div>

    <!-- Metadata -->
    <MetadataSection :metadata="report.metadata" />

    <!-- Limitations (always visible) -->
    <LimitationsBox :items="report.limitations" />

    <!-- Footer: expires + share -->
    <footer class="flex flex-col items-center gap-4 sm:flex-row sm:justify-between rounded-xl border border-gray-200 bg-white px-5 py-4">
      <div class="flex items-center gap-2 text-sm text-gray-500">
        <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span>Expires {{ expiresFormatted }}</span>
      </div>

      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 active:bg-gray-100"
        @click="copyShareLink"
      >
        <!-- Check icon when copied -->
        <svg v-if="copied" class="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        <!-- Link icon default -->
        <svg v-else class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
          />
        </svg>
        {{ copied ? "Copied!" : "Copy share link" }}
      </button>
    </footer>
  </div>
</template>
