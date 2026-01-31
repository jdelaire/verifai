<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { requestUploadToken, uploadFile, finalizeUpload } from "../lib/api";

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/tiff"];
const MAX_SIZE = 5 * 1024 * 1024;

const router = useRouter();
const dragging = ref(false);
const uploading = ref(false);
const error = ref<string | null>(null);
const step = ref<string | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

function validate(file: File): string | null {
  if (!ACCEPTED_TYPES.includes(file.type)) {
    return `Unsupported file type: ${file.type}. Accepted: JPEG, PNG, WebP, TIFF.`;
  }
  if (file.size > MAX_SIZE) {
    return `File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum: 5 MB.`;
  }
  return null;
}

async function handleFile(file: File) {
  error.value = null;
  const validationError = validate(file);
  if (validationError) {
    error.value = validationError;
    return;
  }

  uploading.value = true;
  try {
    step.value = "Requesting upload token...";
    const token = await requestUploadToken(file.type, file.size);

    step.value = "Uploading image...";
    await uploadFile(token.upload_url, file);

    step.value = "Starting analysis...";
    const result = await finalizeUpload(token.job_id);

    router.push(`/report/${result.job_id}`);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Upload failed.";
  } finally {
    uploading.value = false;
    step.value = null;
  }
}

function onDrop(e: DragEvent) {
  dragging.value = false;
  const file = e.dataTransfer?.files[0];
  if (file) handleFile(file);
}

function onFileSelect(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) handleFile(file);
  input.value = "";
}

function openFilePicker() {
  fileInputRef.value?.click();
}
</script>

<template>
  <div
    class="relative rounded-xl border-2 border-dashed p-12 text-center transition-colors"
    :class="[
      dragging ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-gray-400',
      uploading ? 'pointer-events-none opacity-60' : 'cursor-pointer',
    ]"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="onDrop"
    @click="openFilePicker"
  >
    <input
      ref="fileInputRef"
      type="file"
      accept=".jpg,.jpeg,.png,.webp,.tiff,.tif"
      class="hidden"
      @change="onFileSelect"
    />

    <div v-if="uploading" class="space-y-3">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent"></div>
      <p class="text-sm text-gray-600">{{ step }}</p>
    </div>

    <div v-else class="space-y-3">
      <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
        <svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <p class="text-gray-600">
        <span class="font-medium text-indigo-600">Click to upload</span> or drag and drop
      </p>
      <p class="text-xs text-gray-400">JPEG, PNG, WebP, or TIFF up to 5 MB</p>
    </div>

    <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
  </div>
</template>
