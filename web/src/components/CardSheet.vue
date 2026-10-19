<script setup>
import { computed, ref, watch } from "vue";

import { avatarSrc, isOverdue, priorityLabel } from "../copy";
import DateField from "./DateField.vue";
import Menu from "./Menu.vue";

const props = defineProps({
  card: { type: Object, default: null },
  columnId: { type: String, default: "" },
  columns: { type: Array, default: () => [] },
  members: { type: Array, default: () => [] },
  tags: { type: Array, default: () => [] },
  pending: { type: Boolean, default: false },
  error: { type: String, default: "" },
});

const emit = defineEmits(["save", "remove", "close", "toggle-step", "add-step", "remove-step"]);

const title = ref("");
const note = ref("");
const priority = ref("medium");
const dueOn = ref("");
const columnId = ref("");
const memberIds = ref([]);
const tagIds = ref([]);
const draftStep = ref("");
const draftSteps = ref([]);

watch(
  () => props.card,
  (card) => {
    title.value = card?.title ?? "";
    note.value = card?.note ?? "";
    priority.value = card?.priority ?? "medium";
    dueOn.value = card?.due_on ?? "";
    columnId.value = card?.column_id ?? props.columnId;
    memberIds.value = card ? card.members.map((member) => member.id) : [];
    tagIds.value = card ? card.tags.map((tag) => tag.id) : [];
    draftSteps.value = [];
  },
  { immediate: true },
);

const overdue = computed(() => isOverdue(dueOn.value));

const columnLabel = computed(
  () => props.columns.find((column) => column.id === columnId.value)?.title ?? "Колонка",
);
const peopleLabel = computed(() => {
  const picked = props.members.filter((member) => memberIds.value.includes(member.id));
  if (!picked.length) {
    return "Никого";
  }
  if (picked.length === 1) {
    return picked[0].name;
  }
  return `${picked[0].name} и ещё ${picked.length - 1}`;
});
const tagsLabel = computed(() => {
  const picked = props.tags.filter((tag) => tagIds.value.includes(tag.id));
  return picked.length ? picked.map((tag) => tag.name).join(", ") : "Без меток";
});

function toggleMember(id) {
  memberIds.value = memberIds.value.includes(id)
    ? memberIds.value.filter((item) => item !== id)
    : [...memberIds.value, id];
}

function toggleTag(id) {
  tagIds.value = tagIds.value.includes(id)
    ? tagIds.value.filter((item) => item !== id)
    : [...tagIds.value, id];
}

function submit() {
  emit("save", {
    column_id: columnId.value,
    title: title.value,
    note: note.value,
    priority: priority.value,
    due_on: dueOn.value || null,
    member_ids: memberIds.value,
    tag_ids: tagIds.value,
    draft_steps: props.card ? [] : draftSteps.value,
  });
}

function addDraft() {
  const value = draftStep.value.trim();
  if (!value) {
    return;
  }
  if (props.card) {
    emit("add-step", value);
  } else {
    draftSteps.value = [...draftSteps.value, value];
  }
  draftStep.value = "";
}
</script>

<template>
  <div class="sheet-backdrop" @click.self="emit('close')">
    <form class="sheet" @submit.prevent="submit">
      <div class="sheet-head">
        <p class="sheet-kicker">{{ card ? "Задача" : "Новая задача" }}</p>
        <button type="button" class="quiet" @click="emit('close')">Закрыть</button>
      </div>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <input v-model="title" class="sheet-title" required maxlength="160" placeholder="Название" />
      <label class="sheet-note">
        Описание
        <textarea v-model="note" rows="4" maxlength="500" placeholder="Что нужно сделать"></textarea>
      </label>

      <div class="property">
        <span>Колонка</span>
        <Menu v-if="!card">
          <template #trigger>{{ columnLabel }}</template>
          <template #default="{ close }">
            <button
              v-for="column in columns"
              :key="column.id"
              type="button"
              class="menu-item"
              :class="{ 'is-current': column.id === columnId }"
              @click="columnId = column.id; close()"
            >
              {{ column.title }}
            </button>
          </template>
        </Menu>
        <strong v-else>{{ columnLabel }}</strong>
      </div>

      <div class="property">
        <span>Срок</span>
        <div class="due-line">
          <DateField v-model="dueOn" :overdue="overdue" />
          <span v-if="overdue" class="overdue-word">просрочено</span>
        </div>
      </div>

      <div class="property">
        <span>Приоритет</span>
        <Menu>
          <template #trigger>
            <i class="dot" :class="`tone-${priority}`"></i>
            {{ priorityLabel[priority] }}
          </template>
          <template #default="{ close }">
            <button
              v-for="(label, key) in priorityLabel"
              :key="key"
              type="button"
              class="menu-item"
              :class="{ 'is-current': key === priority }"
              @click="priority = key; close()"
            >
              <i class="dot" :class="`tone-${key}`"></i>
              {{ label }}
            </button>
          </template>
        </Menu>
      </div>

      <div class="property">
        <span>Люди</span>
        <Menu>
          <template #trigger>{{ peopleLabel }}</template>
          <template #default>
            <button
              v-for="member in members"
              :key="member.id"
              type="button"
              class="menu-item"
              :class="{ 'is-current': memberIds.includes(member.id) }"
              @click="toggleMember(member.id)"
            >
              <img :src="avatarSrc(member)" :alt="member.name" />
              <span>{{ member.name }}</span>
              <small>{{ member.role }}</small>
            </button>
          </template>
        </Menu>
      </div>

      <div class="property">
        <span>Метки</span>
        <Menu>
          <template #trigger>{{ tagsLabel }}</template>
          <template #default>
            <button
              v-for="tag in tags"
              :key="tag.id"
              type="button"
              class="menu-item"
              :class="{ 'is-current': tagIds.includes(tag.id) }"
              @click="toggleTag(tag.id)"
            >
              <i class="swatch" :class="`swatch-${tag.tone}`"></i>
              {{ tag.name }}
            </button>
          </template>
        </Menu>
      </div>

      <section class="checklist">
        <div class="checklist-head">
          <h2>Подзадачи</h2>
          <span
            v-if="card && card.subtasks.length"
            class="steps"
            :class="{ 'is-complete': card.subtasks.every((item) => item.done) }"
          >
            <i aria-hidden="true"></i>
            {{ card.subtasks.filter((item) => item.done).length }}/{{ card.subtasks.length }}
          </span>
        </div>
        <ul v-if="card">
          <li v-for="step in card.subtasks" :key="step.id">
            <label>
              <input type="checkbox" :checked="step.done" @change="emit('toggle-step', step)" />
              <span :class="{ 'is-done': step.done }">{{ step.title }}</span>
            </label>
            <button type="button" class="quiet step-remove" aria-label="Убрать пункт" @click="emit('remove-step', step)">×</button>
          </li>
        </ul>
        <ul v-else>
          <li v-for="(step, index) in draftSteps" :key="index">
            <span>{{ step }}</span>
            <button type="button" class="quiet step-remove" aria-label="Убрать пункт" @click="draftSteps.splice(index, 1)">×</button>
          </li>
        </ul>
        <div class="draft-step">
          <input v-model="draftStep" maxlength="160" placeholder="Новый пункт" @keydown.enter.prevent="addDraft" />
          <button type="button" class="quiet" @click="addDraft">Добавить</button>
        </div>
      </section>

      <div class="sheet-actions">
        <button type="submit" class="primary" :disabled="pending">
          {{ pending ? "Сохраняю…" : card ? "Сохранить" : "Создать задачу" }}
        </button>
        <button v-if="card" type="button" class="danger" :disabled="pending" @click="emit('remove')">
          Удалить задачу
        </button>
      </div>
    </form>
  </div>
</template>
