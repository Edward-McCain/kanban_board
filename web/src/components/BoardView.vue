<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";

import {
  createCard,
  createColumn,
  createSubtask,
  loadBoard,
  moveCard,
  removeCard,
  removeColumn,
  removeSubtask,
  renameColumn,
  updateCard,
  updateSubtask,
} from "../api";
import { avatarSrc, doneCount, dueLabel, isOverdue, priorityLabel } from "../copy";
import CardSheet from "./CardSheet.vue";
import Menu from "./Menu.vue";

const board = ref({ columns: [], members: [], tags: [] });
const loading = ref(true);
const loadError = ref("");
const notice = ref("");
const query = ref("");
const personId = ref("");
const columnTitle = ref("");
const renaming = ref(null);
const renameValue = ref("");
const sheet = ref(null);
const sheetError = ref("");
const sheetPending = ref(false);
const origin = ref(null);
const dragging = ref(null);
const hover = ref(null);
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const locked = computed(() => query.value.trim().length > 0 || personId.value.length > 0);
const personLabel = computed(
  () => board.value.members.find((member) => member.id === personId.value)?.name ?? "Все",
);

const columns = computed(() => {
  const needle = query.value.trim().toLowerCase();
  return board.value.columns.map((column) => ({
    ...column,
    cards: column.cards.filter((card) => {
      const note = card.note ?? "";
      const matchesQuery =
        !needle ||
        card.title.toLowerCase().includes(needle) ||
        note.toLowerCase().includes(needle);
      const matchesPerson = !personId.value || card.members.some((member) => member.id === personId.value);
      return matchesQuery && matchesPerson;
    }),
  }));
});

function shownCards(column) {
  if (!dragging.value) {
    return column.cards;
  }
  return column.cards.filter((card) => card.id !== dragging.value.card.id);
}

async function reload() {
  board.value = await loadBoard();
  if (sheet.value?.card) {
    const fresh = findCard(sheet.value.card.id);
    if (fresh) {
      sheet.value = { ...sheet.value, card: fresh };
    }
  }
}

function findCard(id) {
  for (const column of board.value.columns) {
    const card = column.cards.find((item) => item.id === id);
    if (card) {
      return card;
    }
  }
  return null;
}

onMounted(async () => {
  window.addEventListener("keydown", onKey);
  try {
    await reload();
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "Доска не ответила.";
  } finally {
    loading.value = false;
  }
});

onUnmounted(() => {
  window.removeEventListener("keydown", onKey);
  stopListening();
});

function onKey(event) {
  if (event.key === "Escape") {
    sheet.value = null;
    cancelDrag();
  }
}

async function addColumn() {
  const title = columnTitle.value.trim();
  if (!title) {
    return;
  }
  notice.value = "";
  try {
    await createColumn(title);
    columnTitle.value = "";
    await reload();
  } catch (error) {
    notice.value = error instanceof Error ? error.message : "Доска не ответила.";
  }
}

function startRename(column) {
  renaming.value = column.id;
  renameValue.value = column.title;
}

async function finishRename(column) {
  if (renaming.value !== column.id) {
    return;
  }
  const title = renameValue.value.trim();
  renaming.value = null;
  if (!title || title === column.title) {
    return;
  }
  try {
    await renameColumn(column.id, title);
    await reload();
  } catch (error) {
    notice.value = error instanceof Error ? error.message : "Доска не ответила.";
  }
}

async function dropColumn(column) {
  notice.value = "";
  try {
    await removeColumn(column.id);
    await reload();
  } catch (error) {
    notice.value = error instanceof Error ? error.message : "Доска не ответила.";
  }
}

function openCreate(columnId) {
  sheetError.value = "";
  const fallback = columnId || board.value.columns[0]?.id || "";
  sheet.value = { columnId: fallback, card: null };
}

function openCard(card) {
  sheetError.value = "";
  sheet.value = { columnId: card.column_id, card };
}

async function saveSheet(payload) {
  if (!sheet.value) {
    return;
  }
  sheetPending.value = true;
  sheetError.value = "";
  const { draft_steps: draftSteps, ...body } = payload;
  try {
    if (sheet.value.card) {
      const { column_id: _columnId, ...changes } = body;
      await updateCard(sheet.value.card.id, changes);
    } else {
      const created = await createCard(body);
      for (const step of draftSteps) {
        await createSubtask(created.id, step);
      }
    }
    await reload();
    sheet.value = null;
  } catch (error) {
    sheetError.value = error instanceof Error ? error.message : "Доска не ответила.";
  } finally {
    sheetPending.value = false;
  }
}

async function deleteCurrent() {
  if (!sheet.value?.card) {
    return;
  }
  sheetPending.value = true;
  sheetError.value = "";
  try {
    await removeCard(sheet.value.card.id);
    await reload();
    sheet.value = null;
  } catch (error) {
    sheetError.value = error instanceof Error ? error.message : "Доска не ответила.";
  } finally {
    sheetPending.value = false;
  }
}

async function toggleStep(step) {
  try {
    await updateSubtask(step.id, { done: !step.done });
    await reload();
  } catch (error) {
    notice.value = error instanceof Error ? error.message : "Доска не ответила.";
  }
}

async function addStep(title) {
  if (!sheet.value?.card) {
    return;
  }
  try {
    await createSubtask(sheet.value.card.id, title);
    await reload();
  } catch (error) {
    sheetError.value = error instanceof Error ? error.message : "Доска не ответила.";
  }
}

async function removeStep(step) {
  try {
    await removeSubtask(step.id);
    await reload();
  } catch (error) {
    sheetError.value = error instanceof Error ? error.message : "Доска не ответила.";
  }
}

function startPointer(event, card) {
  if (locked.value || event.button > 0) {
    return;
  }
  const rect = event.currentTarget.getBoundingClientRect();
  origin.value = {
    pointerId: event.pointerId,
    x: event.clientX,
    y: event.clientY,
    card,
    offsetX: event.clientX - rect.left,
    offsetY: event.clientY - rect.top,
    width: rect.width,
    height: rect.height,
  };
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", onPointerUp);
}

function onPointerMove(event) {
  const start = origin.value;
  if (!start || event.pointerId !== start.pointerId) {
    return;
  }
  const dx = event.clientX - start.x;
  const dy = event.clientY - start.y;
  if (!dragging.value && Math.hypot(dx, dy) < 8) {
    return;
  }
  const lean = event.movementX || dx * 0.02;
  dragging.value = {
    card: start.card,
    offsetX: start.offsetX,
    offsetY: start.offsetY,
    width: start.width,
    height: start.height,
    x: event.clientX,
    y: event.clientY,
    tilt: reducedMotion ? 0 : Math.max(-8, Math.min(8, -4 + lean * 0.35)),
  };
  hover.value = columnUnder(event.clientX, event.clientY, start.card.id);
}

async function onPointerUp(event) {
  const start = origin.value;
  const active = dragging.value;
  const target = hover.value;
  stopListening();
  origin.value = null;
  dragging.value = null;
  hover.value = null;
  if (!start || (event && event.pointerId !== start.pointerId)) {
    return;
  }
  if (!active) {
    openCard(start.card);
    return;
  }
  if (!target) {
    return;
  }
  const samePlace = target.columnId === start.card.column_id && target.index === currentIndex(start.card);
  if (samePlace) {
    return;
  }
  notice.value = "";
  try {
    await moveCard(start.card.id, { column_id: target.columnId, position: target.index });
    await reload();
  } catch (error) {
    notice.value = error instanceof Error ? error.message : "Доска не ответила.";
    await reload();
  }
}

function currentIndex(card) {
  const column = board.value.columns.find((item) => item.id === card.column_id);
  return column ? column.cards.findIndex((item) => item.id === card.id) : 0;
}

function columnUnder(x, y, cardId) {
  const columnEl = document.elementFromPoint(x, y)?.closest("[data-column-id]");
  if (!columnEl) {
    return null;
  }
  const cards = [...columnEl.querySelectorAll("[data-card-id]")].filter(
    (element) => element.dataset.cardId !== cardId,
  );
  let index = cards.length;
  for (let slot = 0; slot < cards.length; slot += 1) {
    const rect = cards[slot].getBoundingClientRect();
    if (y < rect.top + rect.height / 2) {
      index = slot;
      break;
    }
  }
  return { columnId: columnEl.dataset.columnId, index };
}

function cancelDrag() {
  stopListening();
  origin.value = null;
  dragging.value = null;
  hover.value = null;
}

function stopListening() {
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
}

function showPlaceholder(column, index) {
  return hover.value?.columnId === column.id && hover.value.index === index;
}
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="mark" aria-hidden="true"></span>
        <span>
          <strong>Полотно</strong>
          <small>Веб-команда</small>
        </span>
      </div>
      <label class="side-search">
        <input v-model="query" type="search" placeholder="Найти задачу" />
      </label>
      <p class="side-label">Доска</p>
      <p class="side-active">Кабинет</p>
      <p class="side-label">Люди</p>
      <ul class="people">
        <li v-for="member in board.members" :key="member.id">
          <img :src="avatarSrc(member)" :alt="member.name" />
          <span>
            <strong>{{ member.name }}</strong>
            <small>{{ member.role }}</small>
          </span>
        </li>
      </ul>
      <div v-if="board.members[0]" class="me">
        <img :src="avatarSrc(board.members[0])" alt="" />
        <span>
          <strong>{{ board.members[0].name }}</strong>
          <small>{{ board.members[0].role }}</small>
        </span>
      </div>
    </aside>

    <main class="workspace">
      <p v-if="loading" class="status-line">Открываю доску.</p>
      <p v-else-if="loadError" class="form-error" role="alert">{{ loadError }}</p>
      <template v-else>
        <header class="board-head">
          <div>
            <h1>Кабинет</h1>
            <p>Релиз 1.0</p>
          </div>
          <div class="head-tools">
            <Menu align="right">
              <template #trigger>
                <span v-if="personId" class="mini-face">
                  <img :src="avatarSrc(board.members.find((member) => member.id === personId))" alt="" />
                </span>
                {{ personLabel }}
              </template>
              <template #default="{ close }">
                <button type="button" class="menu-item" :class="{ 'is-current': !personId }" @click="personId = ''; close()">
                  Все
                </button>
                <button
                  v-for="member in board.members"
                  :key="member.id"
                  type="button"
                  class="menu-item"
                  :class="{ 'is-current': personId === member.id }"
                  @click="personId = member.id; close()"
                >
                  <img :src="avatarSrc(member)" :alt="member.name" />
                  {{ member.name }}
                </button>
              </template>
            </Menu>
            <button type="button" class="primary" @click="openCreate('')">Новая задача</button>
          </div>
        </header>
        <p v-if="notice" class="form-error" role="alert">{{ notice }}</p>
        <p v-if="locked" class="hint">Пока стоит фильтр, карточки не перетаскиваются.</p>
        <div class="columns">
          <section
            v-for="column in columns"
            :key="column.id"
            class="column"
            :class="[`tone-${column.tone}`, { 'is-target': hover?.columnId === column.id }]"
            :data-column-id="column.id"
          >
            <header class="column-head">
              <div class="column-name">
                <input
                  v-if="renaming === column.id"
                  v-model="renameValue"
                  class="rename"
                  maxlength="80"
                  autofocus
                  @keydown.enter.prevent="($event.target).blur()"
                  @blur="finishRename(column)"
                />
                <button v-else type="button" class="column-title" @click="startRename(column)">
                  {{ column.title }}
                </button>
                <span class="count">{{ column.cards.length }}</span>
              </div>
              <div class="column-tools">
                <button type="button" class="icon-button" aria-label="Карточка в эту колонку" @click="openCreate(column.id)">
                  +
                </button>
                <Menu align="right" :caret="false">
                  <template #trigger><span class="dots" aria-label="Действия колонки">···</span></template>
                  <template #default="{ close }">
                    <button type="button" class="menu-item" @click="startRename(column); close()">
                      Переименовать
                    </button>
                    <button type="button" class="menu-item" @click="dropColumn(column); close()">
                      Убрать колонку
                    </button>
                  </template>
                </Menu>
              </div>
            </header>
            <div class="card-stack">
              <template v-for="(card, index) in shownCards(column)" :key="card.id">
                <div
                  v-if="showPlaceholder(column, index)"
                  class="placeholder"
                  :style="{ height: `${dragging?.height ?? 120}px` }"
                ></div>
                <article
                  class="card"
                  :data-card-id="card.id"
                  role="button"
                  tabindex="0"
                  :aria-label="card.title"
                  @pointerdown="startPointer($event, card)"
                  @keydown.enter.prevent="openCard(card)"
                  @keydown.space.prevent="openCard(card)"
                >
                  <h3>{{ card.title }}</h3>
                  <p v-if="card.note" class="note">{{ card.note }}</p>
                  <div class="card-row">
                    <span v-if="card.due_on" class="due" :class="{ 'is-overdue': isOverdue(card.due_on) }">
                      <time>{{ dueLabel(card.due_on) }}</time>
                      <span v-if="isOverdue(card.due_on)">просрочено</span>
                    </span>
                    <span v-else class="muted">Без срока</span>
                    <span v-if="card.members.length" class="faces">
                      <img
                        v-for="member in card.members"
                        :key="member.id"
                        :src="avatarSrc(member)"
                        :alt="member.name"
                      />
                    </span>
                  </div>
                  <div v-if="card.tags.length || card.priority" class="card-row">
                    <span v-for="tag in card.tags" :key="tag.id" class="tag">
                      <i class="swatch" :class="`swatch-${tag.tone}`"></i>
                      {{ tag.name }}
                    </span>
                    <span class="priority" :class="`is-${card.priority}`">
                      <i class="dot" :class="`tone-${card.priority}`"></i>
                      {{ priorityLabel[card.priority] }}
                    </span>
                  </div>
                  <p
                    v-if="card.subtasks.length"
                    class="steps"
                    :class="{ 'is-complete': doneCount(card) === card.subtasks.length }"
                  >
                    <i aria-hidden="true"></i>
                    {{ doneCount(card) }}/{{ card.subtasks.length }}
                  </p>
                </article>
              </template>
              <div
                v-if="showPlaceholder(column, shownCards(column).length)"
                class="placeholder"
                :style="{ height: `${dragging?.height ?? 120}px` }"
              ></div>
              <button type="button" class="add-card" @click="openCreate(column.id)">Добавить задачу</button>
            </div>
          </section>
          <form class="new-column" @submit.prevent="addColumn">
            <input v-model="columnTitle" maxlength="80" placeholder="Новая колонка" />
            <button type="submit">Добавить</button>
          </form>
        </div>
      </template>
    </main>

    <div
      v-if="dragging"
      class="floater"
      :style="{
        width: `${dragging.width}px`,
        transform: `translate(${dragging.x - dragging.offsetX}px, ${dragging.y - dragging.offsetY}px) rotate(${dragging.tilt}deg)`,
      }"
    >
      <article class="card is-lifted">
        <h3>{{ dragging.card.title }}</h3>
        <p v-if="dragging.card.note" class="note">{{ dragging.card.note }}</p>
      </article>
    </div>

    <CardSheet
      v-if="sheet"
      :card="sheet.card"
      :column-id="sheet.columnId"
      :columns="board.columns"
      :members="board.members"
      :tags="board.tags"
      :pending="sheetPending"
      :error="sheetError"
      @save="saveSheet"
      @remove="deleteCurrent"
      @close="sheet = null"
      @toggle-step="toggleStep"
      @add-step="addStep"
      @remove-step="removeStep"
    />
  </div>
</template>
