
import { parseDatabaseDate } from "../utils/formatting.js";

// Referent table columns for Tabulator

export const REFERENT_TABLE_COLUMNS = [
  {
    field: "moveToPerson",
    // formatter: () => "<button type='button' class='link-refs-add-person-btn' aria-label='Add referent'><i class='fa fa-user-plus'></i></button>",
    formatter: () => "<i class='link-refs-add-person-btn fa fa-user-plus'></i>",
    // width: 40,
    hozAlign: "center",
  },
  {
    title: "Name",
    field: "displayName",
    headerFilter: "input",
    minWidth: 180,
    sorter: "string",
  },
  {
    title: "UUID",
    field: "referent_uuid",
    formatter: (cell) => `<abbr title="${cell.getValue()}">${cell.getValue().slice(0, 6)}</abbr>&hellip;`,
    headerFilter: "input",
    width: 120,
  },
];


// Person table columns for Tabulator
// (with some helper functions)

function formatResearcherLogSummary(logJson) {
  const logEntries = Object.entries(logJson ?? {})
    .sort((a, b) => b[0] - a[0])
    .map(([timestamp, {by, note, type}]) => {
      return { timestamp, by, note, type };
    });

  const summary = logEntries
  .map(({ timestamp, by, note, type }) => `${type}`)
  .join("; ");

  return summary || "No activity";
}

function formatResearcherLogDetails(logJson) {
  const logHTML = Object.entries(logJson ?? {})
  .sort((a, b) => b[0] - a[0])
  .map(([timestamp, {by, note, type}]) => {
    
    timestamp = parseDatabaseDate(timestamp).toLocaleString();

    note = note.replaceAll(/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/g, (match) => {
      return `<abbr title="${match}">${match.slice(0, 4)}</abbr>`;
    });
    note = note.replaceAll('"', "&quot;");
    const popup = `
      <li>
        <strong>${timestamp}: ${type} (${by})</strong>
        <p>${note}</p>
      </li>`;

    return popup;
  }).join("");
  return `<ul>${logHTML}</ul>`;
}


export const PERSON_TABLE_COLUMNS = [
  {
    title: "Status",
    field: "membershipStatus",
    formatter: (cell) => {
      const value = (cell.getValue() ?? "existing").toLowerCase();
      const displayFontAwesomeClass = {
        existing: "fa-user",
        added: "fa-user-plus",
        removed: "fa-user-minus",
      }[value] ?? "fa-user";

      const color = {
        existing: "#555",
        added: "#16a34a",
        removed: "#dc2626",
      }[value] ?? "#555";

      return `<i class="fa ${displayFontAwesomeClass}" style="color: ${color};"></i>`;
    },
    width: 50,
    hozAlign: "center",
  },
  {
    title: "Name",
    field: "displayName",
    headerFilter: "input",
    minWidth: 180,
  },
  {
    title: "UUID",
    field: "referent_uuid",
    formatter: (cell) => `<abbr title="${cell.getValue()}">${cell.getValue().slice(0, 6)}</abbr>&hellip;`,
    headerFilter: "input",
    width: 100,
  },
  {
    title: "Activity log",
    field: "researcher_log",
    formatter: (cell) => formatResearcherLogSummary(cell.getValue()),
    variableHeight: true,
    cellClick: (e, cell) => {
      // const logJson = cell.getValue();
      cell.popup(formatResearcherLogDetails(cell.getValue()), "center");
    },
    width: 300,
  },
  {
    title: "New note (click to edit)",
    field: "notes",
    editor: "textarea",
    editorParams: {
      elementAttributes: {
        maxlength: "255"
      }
    }
  }
];

