<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

const props = defineProps({
  modelValue: { type: String, default: "" },
  overdue: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue"]);

const open = ref(false);
const root = ref(null);
const shownMonth = ref(monthOf(props.modelValue));

watch(
  () => props.modelValue,
  (value) => {
    if (value) {
      shownMonth.value = monthOf(value);
    }
  },
);

const label = computed(() => {
  if (!props.modelValue) {
    return "Выбрать срок";
  }
  const [year, month, day] = props.modelValue.split("-").map(Number);
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
    .format(new Date(year, month - 1, day))
    .replace(".", "");
});

const monthLabel = computed(() =>
  new Intl.DateTimeFormat("ru-RU", { month: "long", year: "numeric" }).format(shownMonth.value),
);

const cells = computed(() => {
  const year = shownMonth.value.getFullYear();
  const month = shownMonth.value.getMonth();
  const offset = (new Date(year, month, 1).getDay() + 6) % 7;
  const count = new Date(year, month + 1, 0).getDate();
  const days = Array.from({ length: offset }, () => null);
  for (let day = 1; day <= count; day += 1) {
    days.push(iso(new Date(year, month, day)));
  }
  return days;
});

function monthOf(value) {
  if (!value) {
    return new Date();
  }
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function iso(date) {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function shift(step) {
  shownMonth.value = new Date(shownMonth.value.getFullYear(), shownMonth.value.getMonth() + step, 1);
}

function pick(value) {
  emit("update:modelValue", value);
  open.value = false;
}

function onPointerDown(event) {
  if (!root.value?.contains(event.target)) {
    open.value = false;
  }
}

onMounted(() => document.addEventListener("pointerdown", onPointerDown));
onUnmounted(() => document.removeEventListener("pointerdown", onPointerDown));
</script>

<template>
  <div ref="root" class="date-field">
    <button type="button" class="menu-trigger" :class="{ 'is-overdue': overdue }" @click="open = !open">
      <span>{{ label }}</span>
    </button>
    <div v-if="open" class="menu-panel date-panel">
      <div class="date-nav">
        <button type="button" @click="shift(-1)" aria-label="Предыдущий месяц">‹</button>
        <strong>{{ monthLabel }}</strong>
        <button type="button" @click="shift(1)" aria-label="Следующий месяц">›</button>
      </div>
      <div class="date-grid weekdays">
        <span v-for="day in ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']" :key="day">{{ day }}</span>
      </div>
      <div class="date-grid">
        <button
          v-for="(day, index) in cells"
          :key="index"
          type="button"
          class="day"
          :class="{ 'is-picked': day && day === modelValue, 'is-empty': !day }"
          :disabled="!day"
          @click="day && pick(day)"
        >
          {{ day ? Number(day.slice(-2)) : "" }}
        </button>
      </div>
      <button v-if="modelValue" type="button" class="quiet date-clear" @click="pick('')">
        Убрать срок
      </button>
    </div>
  </div>
</template>
