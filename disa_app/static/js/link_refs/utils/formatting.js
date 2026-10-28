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

// Parses a date string in the format "YYYY-MM-DD_HHMMSSffffff"
// (what is stored in the database Person logs) and returns a Date object

export function parseDatabaseDate(dateString) {
  const match = dateString.match(
    /^(\d{4})-(\d{2})-(\d{2})_(\d{2})(\d{2})(\d{2})(\d{6})$/,
  );

  if (!match) throw new Error("Invalid date format");

  const [, year, month, day, hour, minute, second, milliseconds] = match;

  return new Date(
    Number(year),
    Number(month) - 1, // Months are zero-based
    Number(day),
    Number(hour),
    Number(minute),
    Number(second),
    Number(milliseconds.slice(0, 3)),
  );
}
