export function displayName(rowData) {
  const name = [rowData.name_first, rowData.name_last]
    .filter((value) => typeof value === "string" && value.trim() !== "")
    .join(" ");

  return name || "[Name once known]";
}

export function displayArray(value) {
  return Array.isArray(value) ? value.join(", ") : "";
}

export function displayDate(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toISOString().slice(0, 10);
}

export function displayLocation(rowData) {
  const properties = rowData.record_locations?.properties;

  if (!properties) {
    return "";
  }

  return [properties.Locale, properties.City, properties["Colony/State"]]
    .filter(Boolean)
    .join(", ");
}

export function pluralizeReferents(count) {
  return `${count} referent${count === 1 ? "" : "s"}`;
}
