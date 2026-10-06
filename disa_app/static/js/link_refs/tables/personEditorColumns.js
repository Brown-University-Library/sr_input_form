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
    title: "Notes",
    field: "notes",
    editor: "textarea",
    editorParams: {
      elementAttributes: {
        maxlength: "255"
      }
    }
  }
];

export const PERSON_ADD_TABLE_COLUMNS = [
  {
    formatter: () => "<i class='fa fa-xmark'></i>",
    width: 40,
    hozAlign: "center",
  },
  {
    title: "Name",
    field: "displayName",
  },
  {
    title: "UUID",
    field: "referent_uuid",
  },
  {
    title: "Notes",
    field: "notes",
    editor: "textarea",
    editorParams: {
      elementAttributes: {
        maxlength: "255",
      },
    },
  },
];

export const PERSON_REMOVE_TABLE_COLUMNS = [
  {
    formatter: () => "<i class='fa fa-xmark'></i>",
    width: 40,
    hozAlign: "center",
  },
  {
    title: "Name",
    field: "displayName",
  },
  {
    title: "UUID",
    field: "referent_uuid",
  },
  {
    title: "Notes",
    field: "notes",
    editor: "textarea",
    editorParams: {
      elementAttributes: {
        maxlength: "255",
      },
    },
  },
];
