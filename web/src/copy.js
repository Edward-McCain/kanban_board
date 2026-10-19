export const priorityLabel = {
  low: "Низкий",
  medium: "Средний",
  high: "Высокий",
  urgent: "Срочно",
};

export function isOverdue(value) {
  if (!value) {
    return false;
  }
  const [year, month, day] = value.split("-").map(Number);
  const due = new Date(year, month - 1, day);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return due < today;
}

export function dueLabel(value) {
  if (!value) {
    return "";
  }
  const [year, month, day] = value.split("-").map(Number);
  const formatted = new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
  }).format(new Date(year, month - 1, day));
  return formatted.replace(".", "");
}

export function avatarSrc(member) {
  return `/avatars/${member.avatar}`;
}

export function doneCount(card) {
  return card.subtasks.filter((item) => item.done).length;
}
