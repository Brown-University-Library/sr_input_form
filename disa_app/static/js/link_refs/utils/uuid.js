export function formatUuid(value) {
  if (!value || typeof value !== "string") {
    return value;
  }

  const hex = value.replace(/[^a-fA-F0-9]/g, "");

  if (hex.length !== 32) {
    return value;
  }

  return [
    hex.slice(0, 8),
    hex.slice(8, 12),
    hex.slice(12, 16),
    hex.slice(16, 20),
    hex.slice(20),
  ].join("-").toLowerCase();
}

export function unformatUuid(value) {
  if (!value || typeof value !== "string") {
    return value;
  }

  return value.replace(/-/g, "").toLowerCase();
}
