const headers = { "Content-Type": "application/json" };

async function send(path, options) {
  const response = await fetch(path, options);
  if (response.status === 204) {
    return null;
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(body?.error?.message ?? "Доска не ответила.");
  }
  return body;
}

export function loadBoard() {
  return send("/api/board");
}

export function createColumn(title) {
  return send("/api/columns", {
    method: "POST",
    headers,
    body: JSON.stringify({ title }),
  });
}

export function renameColumn(id, title) {
  return send(`/api/columns/${id}`, {
    method: "PATCH",
    headers,
    body: JSON.stringify({ title }),
  });
}

export function removeColumn(id) {
  return send(`/api/columns/${id}`, { method: "DELETE" });
}

export function createCard(payload) {
  return send("/api/cards", {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
}

export function updateCard(id, payload) {
  return send(`/api/cards/${id}`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(payload),
  });
}

export function moveCard(id, payload) {
  return send(`/api/cards/${id}/move`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
}

export function removeCard(id) {
  return send(`/api/cards/${id}`, { method: "DELETE" });
}

export function createSubtask(cardId, title) {
  return send(`/api/cards/${cardId}/subtasks`, {
    method: "POST",
    headers,
    body: JSON.stringify({ title }),
  });
}

export function updateSubtask(id, payload) {
  return send(`/api/subtasks/${id}`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(payload),
  });
}

export function removeSubtask(id) {
  return send(`/api/subtasks/${id}`, { method: "DELETE" });
}
