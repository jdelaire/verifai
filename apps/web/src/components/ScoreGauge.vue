<script setup lang="ts">
import { computed } from "vue";
import type { ConfidenceTier } from "@verifai/shared/src/types";

const props = defineProps<{
  score: number;
  confidence: ConfidenceTier;
}>();

const radius = 70;
const stroke = 10;
const normalizedRadius = radius - stroke / 2;
const circumference = 2 * Math.PI * normalizedRadius;

const dashOffset = computed(() => {
  const pct = Math.max(0, Math.min(100, props.score)) / 100;
  return circumference - pct * circumference;
});

const scoreColor = computed(() => {
  if (props.score <= 30) return { ring: "#22c55e", text: "text-green-600", bg: "bg-green-50" };
  if (props.score <= 60) return { ring: "#eab308", text: "text-yellow-600", bg: "bg-yellow-50" };
  return { ring: "#ef4444", text: "text-red-600", bg: "bg-red-50" };
});

const scoreLabel = computed(() => {
  if (props.score <= 30) return "Likely authentic";
  if (props.score <= 60) return "Uncertain";
  return "Likely AI-generated";
});

const confidenceBadge = computed(() => {
  switch (props.confidence) {
    case "high":
      return { label: "High confidence", classes: "bg-green-100 text-green-800" };
    case "medium":
      return { label: "Medium confidence", classes: "bg-yellow-100 text-yellow-800" };
    case "low":
      return { label: "Low confidence", classes: "bg-orange-100 text-orange-800" };
    default:
      return { label: "Unknown", classes: "bg-gray-100 text-gray-600" };
  }
});
</script>

<template>
  <div class="flex flex-col items-center gap-4">
    <!-- SVG gauge -->
    <div class="relative inline-flex items-center justify-center">
      <svg
        :width="radius * 2"
        :height="radius * 2"
        class="transform -rotate-90"
      >
        <!-- Background ring -->
        <circle
          :cx="radius"
          :cy="radius"
          :r="normalizedRadius"
          fill="none"
          :stroke-width="stroke"
          stroke="#e5e7eb"
        />
        <!-- Score ring -->
        <circle
          :cx="radius"
          :cy="radius"
          :r="normalizedRadius"
          fill="none"
          :stroke-width="stroke"
          stroke-linecap="round"
          :stroke="scoreColor.ring"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="dashOffset"
          class="transition-[stroke-dashoffset] duration-1000 ease-out"
        />
      </svg>

      <!-- Center text -->
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span
          class="text-3xl font-bold tabular-nums"
          :class="scoreColor.text"
        >
          {{ props.score }}
        </span>
        <span class="text-xs text-gray-400 font-medium">/ 100</span>
      </div>
    </div>

    <!-- Score label -->
    <p class="text-sm font-medium text-gray-600">{{ scoreLabel }}</p>

    <!-- Confidence badge -->
    <span
      class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold"
      :class="confidenceBadge.classes"
    >
      <span
        class="h-1.5 w-1.5 rounded-full"
        :class="[
          props.confidence === 'high' ? 'bg-green-500' : '',
          props.confidence === 'medium' ? 'bg-yellow-500' : '',
          props.confidence === 'low' ? 'bg-orange-500' : '',
        ]"
      ></span>
      {{ confidenceBadge.label }}
    </span>
  </div>
</template>
