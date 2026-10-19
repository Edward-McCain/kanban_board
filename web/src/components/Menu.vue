<script setup>
import { onMounted, onUnmounted, ref } from "vue";

defineProps({
  align: { type: String, default: "left" },
  caret: { type: Boolean, default: true },
});

const open = ref(false);
const root = ref(null);

function onPointerDown(event) {
  if (!root.value?.contains(event.target)) {
    open.value = false;
  }
}

onMounted(() => document.addEventListener("pointerdown", onPointerDown));
onUnmounted(() => document.removeEventListener("pointerdown", onPointerDown));

function close() {
  open.value = false;
}

defineExpose({ close });
</script>

<template>
  <div ref="root" class="menu" :class="{ 'is-open': open }">
    <button type="button" class="menu-trigger" @click="open = !open">
      <slot name="trigger" />
      <svg v-if="caret" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M4 6.2 8 10l4-3.8" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
      </svg>
    </button>
    <div v-if="open" class="menu-panel" :class="`align-${align}`">
      <slot :close="close" />
    </div>
  </div>
</template>
