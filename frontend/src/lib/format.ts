export function formatDate(dateString?: string) {
  if (!dateString) return "Unknown";

  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return "Unknown";

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export function formatRelativeCount(value?: number) {
  if (value == null) return "0";
  return new Intl.NumberFormat("en-US").format(value);
}

export function getInitials(...values: Array<string | undefined>) {
  const joined = values
    .filter(Boolean)
    .map((value) => value!.trim())
    .filter(Boolean);

  if (joined.length === 0) return "--";

  return joined
    .slice(0, 2)
    .map((value) => value[0]?.toUpperCase() ?? "")
    .join("");
}
