<script setup lang="ts">
import { computed } from "vue";
import type { ImageMetadata } from "@verifai/shared/src/types";

const props = defineProps<{
  metadata: ImageMetadata;
}>();

const fields = computed(() => [
  {
    label: "EXIF data",
    value: props.metadata.has_exif ? "Present" : "Not available",
    highlight: props.metadata.has_exif,
  },
  {
    label: "Camera",
    value: props.metadata.camera_make_model ?? "Not available",
    highlight: !!props.metadata.camera_make_model,
  },
  {
    label: "Software",
    value: props.metadata.software_tag ?? "Not available",
    highlight: !!props.metadata.software_tag,
  },
  {
    label: "Dimensions",
    value: `${props.metadata.width} x ${props.metadata.height} px`,
    highlight: true,
  },
  {
    label: "Format",
    value: props.metadata.format.toUpperCase(),
    highlight: true,
  },
]);
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
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        Image Metadata
      </h3>
    </div>

    <!-- Body -->
    <div class="px-5 py-4">
      <dl class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="field in fields"
          :key="field.label"
          class="rounded-lg bg-gray-50 px-4 py-3"
        >
          <dt class="text-xs font-medium uppercase tracking-wider text-gray-400">
            {{ field.label }}
          </dt>
          <dd
            class="mt-1 text-sm font-medium"
            :class="field.highlight ? 'text-gray-800' : 'text-gray-400 italic'"
          >
            {{ field.value }}
          </dd>
        </div>
      </dl>
    </div>
  </section>
</template>
