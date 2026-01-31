<script setup lang="ts">
import { ref, watch, onUnmounted } from "vue";

const props = defineProps<{
  status: "pending" | "processing";
}>();

const activeStep = ref(0);
let interval: ReturnType<typeof setInterval> | null = null;

function startStepping() {
  activeStep.value = 1;
  interval = setInterval(() => {
    activeStep.value = activeStep.value >= 3 ? 1 : activeStep.value + 1;
  }, 2400);
}

function stopStepping() {
  if (interval) {
    clearInterval(interval);
    interval = null;
  }
  activeStep.value = 0;
}

watch(
  () => props.status,
  (val) => {
    if (val === "processing") {
      startStepping();
    } else {
      stopStepping();
    }
  },
  { immediate: true },
);

onUnmounted(() => stopStepping());

const steps = [
  { num: 1, label: "Extracting metadata" },
  { num: 2, label: "Checking provenance" },
  { num: 3, label: "Running AI detection" },
];
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 space-y-8">
    <!-- Spinner -->
    <div class="relative h-16 w-16">
      <div
        class="absolute inset-0 rounded-full border-4 border-gray-200"
      ></div>
      <div
        class="absolute inset-0 rounded-full border-4 border-indigo-600 border-t-transparent animate-spin"
      ></div>
    </div>

    <!-- Status headline -->
    <p
      v-if="props.status === 'pending'"
      class="text-lg font-medium text-gray-500"
    >
      Waiting to start...
    </p>
    <p
      v-else
      class="text-lg font-medium text-gray-700"
    >
      Analyzing your image
    </p>

    <!-- Step indicators -->
    <ol class="w-full max-w-sm space-y-3">
      <li
        v-for="step in steps"
        :key="step.num"
        class="flex items-center gap-3 rounded-lg px-4 py-3 transition-all duration-300"
        :class="[
          activeStep === step.num
            ? 'bg-indigo-50 ring-1 ring-indigo-200'
            : activeStep > step.num
              ? 'bg-gray-50'
              : 'bg-white',
        ]"
      >
        <!-- Step circle -->
        <span
          class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition-colors duration-300"
          :class="[
            activeStep === step.num
              ? 'bg-indigo-600 text-white'
              : activeStep > step.num
                ? 'bg-green-500 text-white'
                : 'bg-gray-200 text-gray-500',
          ]"
        >
          <svg
            v-if="activeStep > step.num"
            class="h-3.5 w-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="3"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <span v-else>{{ step.num }}</span>
        </span>

        <!-- Step label -->
        <span
          class="text-sm font-medium transition-colors duration-300"
          :class="[
            activeStep === step.num
              ? 'text-indigo-700'
              : activeStep > step.num
                ? 'text-green-700'
                : 'text-gray-400',
          ]"
        >
          {{ step.label }}
        </span>

        <!-- Animated dots for active step -->
        <span
          v-if="activeStep === step.num"
          class="ml-auto flex gap-0.5"
        >
          <span class="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
          <span class="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse [animation-delay:150ms]"></span>
          <span class="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse [animation-delay:300ms]"></span>
        </span>
      </li>
    </ol>
  </div>
</template>
