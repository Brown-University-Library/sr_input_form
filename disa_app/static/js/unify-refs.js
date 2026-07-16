//const DATA_URL = "data.json";

// Global variables for count elements and error message

const availableCountElement = document.querySelector("#available-count"),
  selectedCountElement = document.querySelector("#selected-count"),
  errorElement = document.querySelector("#error-message");

// Tabulator options

const columns = [
  {
    title: "",
    field: "drag_handle",
    formatter: "handle",
    rowHandle: true,
    headerSort: false,
    resizable: false,
    frozen: true,
    width: 40,
  },
  {
    title: "Name",
    field: "displayName",
    headerFilter: "input",
    formatter: (cell) => displayName(cell.getRow().getData()),
    sorter: (a, b, aRow, bRow) => {
      const aName = displayName(aRow.getData());
      const bName = displayName(bRow.getData());

      return aName.localeCompare(bName);
    },
    minWidth: 180,
  },
  {
    title: "UUID",
    field: "referent_uuid",
    headerFilter: "input",
    width: 100,
  },
  {
    title: "Sex",
    field: "sex",
    headerFilter: "input",
    width: 100,
  },
  {
    title: "Age",
    field: "age",
    headerFilter: "input",
    minWidth: 120,
  },
  {
    title: "Age Category",
    field: "age_category",
    headerFilter: "input",
    minWidth: 150,
  },
  {
    title: "Race",
    field: "races",
    formatter: (cell) => displayArray(cell.getValue()),
    headerFilter: "input",
    minWidth: 140,
  },
  {
    title: "Tribes",
    field: "tribes",
    formatter: (cell) => displayArray(cell.getValue()),
    headerFilter: "input",
    minWidth: 160,
  },
  {
    title: "Origins",
    field: "origins",
    formatter: (cell) => displayArray(cell.getValue()),
    headerFilter: "input",
    minWidth: 160,
  },
  {
    title: "Occupations",
    field: "occupations",
    formatter: (cell) => displayArray(cell.getValue()),
    headerFilter: "input",
    minWidth: 160,
  },
  {
    title: "Enslavement Status",
    field: "enslavement_status",
    formatter: (cell) => displayArray(cell.getValue()),
    headerFilter: "input",
    minWidth: 260,
  },
  {
    title: "Record Type",
    field: "record_type",
    headerFilter: "input",
    minWidth: 160,
  },
  {
    title: "National Context",
    field: "record_national_context",
    headerFilter: "input",
    minWidth: 160,
  },
  {
    title: "Record Date",
    field: "record_date",
    formatter: (cell) => displayDate(cell.getValue()),
    headerFilter: "input",
    width: 130,
  },
  {
    title: "Location",
    field: "record_locations",
    formatter: (cell) => displayLocation(cell.getRow().getData()),
    headerFilter: "input",
    minWidth: 220,
  },
  {
    title: "Record ID",
    field: "record_id",
    headerFilter: "input",
    width: 110,
  },
];

const sharedTableOptions = {
  index: "referent_uuid",
  layout: "fitDataStretch",
  movableRows: true,
  movableRowsReceiver: "add",
  movableRowsSender: "delete",
  placeholder: "No referents",
  columns,
};

const unifiedTableOptions = {
  ...sharedTableOptions,
  data: [],
  height: "300px",
  movableRowsConnectedTables: "#remaining-table",
};

const remainingTableOptions = {
  ...sharedTableOptions,
  height: "600px",
  movableRowsConnectedTables: "#selected-table",
};

// Functions

function displayArray(value) {
  return Array.isArray(value) ? value.join(", ") : "";
}

function displayName(rowData) {
  const name = [rowData.name_first, rowData.name_last]
    .filter((value) => typeof value === "string" && value.trim() !== "")
    .join(" ");

  return name || "[Unnamed]";
}

function displayDate(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toISOString().slice(0, 10);
}

function displayLocation(rowData) {
  const properties = rowData.record_locations?.properties;

  if (!properties) {
    return "";
  }

  return [properties.Locale, properties.City, properties["Colony/State"]]
    .filter(Boolean)
    .join(", ");
}

// Normalize UUID strings by inserting hyphens if they are 32 hex chars.

function formatUuid(value) {
  if (!value || typeof value !== "string") {
    return value;
  }

  // Strip non-hex characters (in case UUIDs already contain hyphens or unexpected chars)
  const hex = value.replace(/[^a-fA-F0-9]/g, "");

  if (hex.length !== 32) {
    // Not a compact UUID candidate; return original value unchanged
    return value;
  }

  return (
    hex.slice(0, 8) +
    "-" +
    hex.slice(8, 12) +
    "-" +
    hex.slice(12, 16) +
    "-" +
    hex.slice(16, 20) +
    "-" +
    hex.slice(20)
  ).toLowerCase();
}

function pluralizeReferents(count) {
  return `${count} referent${count === 1 ? "" : "s"}`;
}

function updateCounts(remainingTable, unifiedTable) {
  availableCountElement.textContent = pluralizeReferents(
    remainingTable.getDataCount(),
  );

  selectedCountElement.textContent = pluralizeReferents(
    unifiedTable.getDataCount(),
  );
}

function showError(message) {
  errorElement.textContent = message;
  errorElement.hidden = false;
}

function main() {
  /*
   * Create the selected table
   */
  const unifiedTable = new Tabulator("#selected-table", unifiedTableOptions);

  /*
   * Create the remaining table, loading data from data.json and normalizing UUIDs
   */
  const remainingTable = new Tabulator("#remaining-table", {
    ...remainingTableOptions,

    ajaxURL: DATA_URL,

    ajaxResponse(url, params, response) {
      if (!response || !Array.isArray(response.referent_list)) {
        throw new Error(
          "data.json must contain a top-level referent_list array.",
        );
      }

      console.log("Data metadata:", response.meta);

      // Ensure `referent_uuid` values are normalized to UUID hyphenation
      const list = response.referent_list.map((item) => {
        return Object.assign({}, item, {
          referent_uuid: formatUuid(item.referent_uuid),
          displayName: displayName(item),
        });
      });

      return list;
    },
  });

  const updateCountsWithTables = () =>
    updateCounts(remainingTable, unifiedTable);

  remainingTable.on("dataLoaded", updateCountsWithTables);
  unifiedTable.on("dataLoaded", updateCountsWithTables);

  remainingTable.on("rowAdded", updateCountsWithTables);
  remainingTable.on("rowDeleted", updateCountsWithTables);

  unifiedTable.on("rowAdded", updateCountsWithTables);
  unifiedTable.on("rowDeleted", updateCountsWithTables);

  remainingTable.on("movableRowsReceived", updateCountsWithTables);
  unifiedTable.on("movableRowsReceived", updateCountsWithTables);

  remainingTable.on("dataLoadError", (error) => {
    console.error("Could not load data.json:", error);

    availableCountElement.textContent = "Unable to load referents";

    showError(
      "Could not load data.json. Make sure the file is in the same " +
        "directory as this HTML file and that the directory is being " +
        "served through a local web server.",
    );
  });
}

main();
