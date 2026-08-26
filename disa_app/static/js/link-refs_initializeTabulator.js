//const DATA_URL = "data.json";

// Global variables for count elements and error message

const availableCountElement = document.querySelector("#available-count"),
  selectedCountElement = document.querySelector("#selected-count"),
  saveStatusElement = document.querySelector("#save-status-message");

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

const linkedReferentsTableOptions = {
  ...sharedTableOptions,
  data: [],
  height: "300px",
  movableRowsConnectedTables: "#remaining-table",
};

const remainingReferentsTableOptions = {
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

function unformatUuid(value) {
  if (!value || typeof value !== "string") {
    return value;
  } else {
    return value.replace(/-/g, "").toLowerCase();
  }
}

function pluralizeReferents(count) {
  return `${count} referent${count === 1 ? "" : "s"}`;
}

function updateCounts(remainingReferentsTable, linkedReferentsTable) {
  availableCountElement.textContent = pluralizeReferents(
    remainingReferentsTable.getDataCount(),
  );

  selectedCountElement.textContent = pluralizeReferents(
    linkedReferentsTable.getDataCount(),
  );
}

function showSaveStatus(message) {
  saveStatusElement.textContent = message;
  saveStatusElement.hidden = false;
}

// Get CSRF token from cookies for Django form submission

function getCsrftoken() {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; csrftoken=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return "";
}

// Gets link-referents form submission handler

function getLinkReferentClickHandler(
  linkedReferentsTable,
  remainingReferentsTable,
  linkReferentsForm,
) {
  const researcherNote = document.getElementById("researcher-note");

  // Submit the Link Referents form data to the API

  function submitToServer(payload) {
    fetch("/data/person/link-referents/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrftoken(),
      },
      body: JSON.stringify(payload),
    }).then(async (response) => {
      if (response.ok) {

        // TODO: get the response data and save it to variable newPersonUuid
        const responseData = await response.json();
        const newPersonUuid = responseData.person_uuid;

        // Clear and reset the tables and form after successful submission
        linkedReferentsTable.clearData();
        remainingReferentsTable.destroy();
        remainingReferentsTable = initializeRemainingReferentsTable();
        researcherNote.value = "";
        updateCounts(remainingReferentsTable, linkedReferentsTable);
        showSaveStatus("Referents linked successfully. New Person UUID: " + newPersonUuid);

        return;
      }

      const error = await response.text();
      alert("Error Linking Referents: " + error);
      throw new Error(error);
    });
  }

  return (event) => {
    event.preventDefault();
    const linkedReferentsUuid = linkedReferentsTable
      .getData()
      .map((item) => unformatUuid(item.referent_uuid));

    if (linkedReferentsUuid.length > 1) {
      // Prepare the payload for submission
      const payload = {
        researcher_note: researcherNote.value,
        referent_uuids: linkedReferentsUuid,
      };
      submitToServer(payload);
    }
  };
}

// Initialize the Linked Referents Tabulator table

function initializeLinkedReferentsTable() {
  return new Tabulator("#selected-table", linkedReferentsTableOptions);
}

// Initialize the Remaining Referents Tabulator table

function initializeRemainingReferentsTable() {
  return new Tabulator("#remaining-table", {
    ...remainingReferentsTableOptions,

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
}

function initializeTablesAndEventHandlers(linkReferentsForm) {
  // Create Tabulator tables

  const linkedReferentsTable = initializeLinkedReferentsTable(),
    remainingReferentsTable = initializeRemainingReferentsTable();

  // Update counts and activate/deactivate the submission
  // form when data is loaded or rows are added/removed

  const updateCountsWithTables = () => {
    linkReferentsForm.disabled = linkedReferentsTable.getDataCount() < 2;
    updateCounts(remainingReferentsTable, linkedReferentsTable);
  };

  remainingReferentsTable.on("dataLoaded", updateCountsWithTables);
  linkedReferentsTable.on("dataLoaded", updateCountsWithTables);

  remainingReferentsTable.on("rowAdded", updateCountsWithTables);
  remainingReferentsTable.on("rowDeleted", updateCountsWithTables);

  linkedReferentsTable.on("rowAdded", updateCountsWithTables);
  linkedReferentsTable.on("rowDeleted", updateCountsWithTables);

  remainingReferentsTable.on("movableRowsReceived", updateCountsWithTables);
  linkedReferentsTable.on("movableRowsReceived", updateCountsWithTables);

  remainingReferentsTable.on("dataLoadError", (error) => {
    console.error("Could not load data.json:", error);

    availableCountElement.textContent = "Unable to load referents";

    showSaveStatus(
      "Could not load data.json. Make sure the file is in the same " +
        "directory as this HTML file and that the directory is being " +
        "served through a local web server.",
    );
  });

  return { linkedReferentsTable, remainingReferentsTable };
}

function initializeTabulatorTables() {

  // Handle form submission

  const linkReferentsForm = document.getElementById(
    "link-referents-form-fieldset",
  );
  const linkReferentsFormElement = document.getElementById(
    "link-referents-form",
  );

  // Initialize the tables

  const { linkedReferentsTable, remainingReferentsTable } =
    initializeTablesAndEventHandlers(linkReferentsForm);


  linkReferentsFormElement.addEventListener(
    "submit",
    getLinkReferentClickHandler(
      linkedReferentsTable,
      remainingReferentsTable,
      linkReferentsForm,
    ),
  );
}

export { initializeTabulatorTables }
