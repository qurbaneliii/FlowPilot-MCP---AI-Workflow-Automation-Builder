export function titleCase(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function formatTimestamp(value?: string | null): string {
  if (!value) return "Not recorded";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    month: "short",
    day: "numeric"
  }).format(date);
}

export function formatShortId(value?: string | null): string {
  if (!value) return "n/a";
  return value.length > 12 ? `${value.slice(0, 8)}...${value.slice(-4)}` : value;
}

export function pluralize(count: number, singular: string, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

export function summarizeUnknown(value: unknown): string {
  if (value == null) return "No output yet";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return pluralize(value.length, "item");
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    if (typeof record.summary === "string") return record.summary;
    if (Array.isArray(record.findings)) return pluralize(record.findings.length, "finding");
    if (Array.isArray(record.issue_drafts)) {
      return pluralize(record.issue_drafts.length, "issue draft");
    }
    if (Array.isArray(record.issues)) return pluralize(record.issues.length, "issue");
    if (Array.isArray(record.artifacts)) return pluralize(record.artifacts.length, "artifact");
    if (Array.isArray(record.created_issues)) {
      return pluralize(record.created_issues.length, "created issue");
    }
    if (typeof record.post_text === "string") return "LinkedIn draft generated";
    return `${Object.keys(record).length} output field(s)`;
  }
  return "Output captured";
}

export function copyToClipboard(text: string): Promise<void> {
  if (!navigator.clipboard) {
    return Promise.reject(new Error("Clipboard API is unavailable."));
  }
  return navigator.clipboard.writeText(text);
}
