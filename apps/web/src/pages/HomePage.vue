<script setup lang="ts">
import UploadZone from "../components/UploadZone.vue";
</script>

<template>
  <div class="space-y-8">
    <section class="text-center">
      <h1 class="text-4xl font-extrabold tracking-tight text-gray-900">
        VerifAI
      </h1>
      <p class="mt-3 text-lg text-gray-500">
        Upload an image to estimate the likelihood it was AI-generated.
      </p>
    </section>

    <UploadZone />

    <section class="rounded-lg bg-amber-50 border border-amber-200 p-4 text-sm text-amber-800">
      <p class="font-medium">How it works</p>
      <ol class="mt-2 list-decimal list-inside space-y-1 text-amber-700">
        <li>Upload an image (JPEG, PNG, WebP, or TIFF)</li>
        <li>We extract metadata, check provenance, and run AI detection</li>
        <li>You get a report with an AI likelihood score and confidence level</li>
      </ol>
      <p class="mt-2 text-xs text-amber-600">
        Results are probabilistic estimates, not definitive proof. Images are deleted after analysis.
      </p>
    </section>
  </div>
</template>
