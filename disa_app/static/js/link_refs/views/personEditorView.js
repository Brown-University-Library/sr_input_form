import { qs, setHidden } from "../utils/dom.js";
import { formatUuid } from "../utils/uuid.js";
import { SELECTOR_IDS } from "../constants.js";
import {
  REFERENT_TABLE_COLUMNS,
  PERSON_TABLE_COLUMNS,
} from "../tables/index.js";

export class PersonEditorView {
  constructor() {
    this.personTableRoot = qs(`#${SELECTOR_IDS.PERSON_TABLE}`);
    this.personTableChangeControllers = qs(`#${SELECTOR_IDS.PERSON_TABLE_CHANGE_CONTROLLERS}`);
    this.referentTableRoot = qs(`#${SELECTOR_IDS.REFERENT_TABLE}`);
    this.submitButton = qs(`#${SELECTOR_IDS.SUBMIT_PERSON_CHANGES}`);
    this.cancelButton = qs(`#${SELECTOR_IDS.CANCEL_PERSON_CHANGES}`);
    this.personUuidElem = qs(`#${SELECTOR_IDS.PERSON_UUID}`);
    this.saveStatusElem = qs(`#${SELECTOR_IDS.SAVE_STATUS_MESSAGE}`);
    this.changePersonButton = qs(`#${SELECTOR_IDS.CHANGE_PERSON_BUTTON}`);
    this.newPersonButton_editView = qs(`#${SELECTOR_IDS.CREATE_NEW_PERSON_BUTTON_EDIT_VIEW}`);

    this.handlers = {};
    this.tables = {
      referent: null,
      person: null,
    };

    this.handleReferentAddClick = this.handleReferentAddClick.bind(this);
    this.handlePersonMembershipClick = this.handlePersonMembershipClick.bind(this);
  }

  bindEvents({ onSaveChanges, onCancelChanges, onPersonDataChanged, onChangePerson, onCreateNewPerson }) {
    this.handlers.onSaveChanges = onSaveChanges;
    this.handlers.onCancelChanges = onCancelChanges;
    this.handlers.onPersonDataChanged = onPersonDataChanged;
    this.handlers.onChangePerson = onChangePerson;
    this.handlers.onCreateNewPerson = onCreateNewPerson;

    if (this.submitButton) {
      this.submitButton.addEventListener("click", () => {
        this.handlers.onSaveChanges?.();
      });
    }

    if (this.cancelButton) {
      this.cancelButton.addEventListener("click", () => {
        this.handlers.onCancelChanges?.();
      });
    }

    if (this.changePersonButton) {
      this.changePersonButton.addEventListener("click", () => {
        this.handlers.onChangePerson?.();
      });
    }

    if (this.newPersonButton_editView) {
      this.newPersonButton_editView.addEventListener("click", () => {
        this.handlers.onCreateNewPerson?.();
      });
    }
  }

  notifyPersonDataChanged() {
    if (!this.tables.person || typeof this.tables.person.getData !== "function") {
      return;
    }

    const rows = this.tables.person.getData() ?? [];
    this.handlers.onPersonDataChanged?.(rows);
    this.updateChangeControllersVisibility();
  }

  handleReferentAddClick(event, cell) {
    const columnDef = cell?.getColumn?.().getDefinition?.() ?? {};

    if (columnDef.field !== "moveToPerson") {
      return;
    }

    const personTable = this.tables.person;
    const referentTable = this.tables.referent;

    if (!personTable || !referentTable) {
      return;
    }

    const rowData = cell.getRow().getData();
    const targetUuid = formatUuid(rowData?.referent_uuid);

    if (!targetUuid) {
      return;
    }

    const personRows = [...(personTable.getData?.() ?? [])];
    const referentRows = [...(referentTable.getData?.() ?? [])];

    const nextReferentRows = referentRows.filter(
      (row) => formatUuid(row?.referent_uuid) !== targetUuid,
    );

    const nextPersonRows = [...personRows, { ...rowData, membershipStatus: "added" }];

    personTable.setData(nextPersonRows);
    referentTable.setData(nextReferentRows);
    this.notifyPersonDataChanged();
  }

  handlePersonMembershipClick(event, cell) {
    const columnDef = cell?.getColumn?.().getDefinition?.() ?? {};

    if (columnDef.field !== "membershipStatus") {
      return;
    }

    const personTable = this.tables.person;
    const referentTable = this.tables.referent;
    const rowData = cell.getRow().getData();
    const rowUuid = formatUuid(rowData?.referent_uuid);

    if (!personTable || !rowUuid) {
      return;
    }

    const currentStatus = (rowData?.membershipStatus ?? "existing").toLowerCase();
    const allRows = [...(personTable.getData?.() ?? [])];

    if (currentStatus === "added") {
      const nextPersonRows = allRows.filter(
        (row) => formatUuid(row?.referent_uuid) !== rowUuid,
      );
      const referentRows = [...(referentTable?.getData?.() ?? [])];
      const nextReferentRows = [...referentRows, { ...rowData }];

      personTable.setData(nextPersonRows);
      referentTable?.setData(nextReferentRows);
      this.notifyPersonDataChanged();
      return;
    }

    const nextStatus = currentStatus === "existing" ? "removed" : "existing";
    const nextRows = allRows.map((row) => {
      if (formatUuid(row?.referent_uuid) !== rowUuid) {
        return row;
      }

      return {
        ...row,
        membershipStatus: nextStatus,
      };
    });

    personTable.setData(nextRows);
    this.notifyPersonDataChanged();
  }

  render(state) {

    console.log("Rendering person editor view with state:", state);

    const truncateUuid = (value) => {
      if (!value || typeof value !== "string") {
        return "";
      }

      const shortValue = value.replace(/-/g, "");
      return shortValue.length <= 6 ? value : `${shortValue.slice(0, 6)}…`;
    };

    if (this.personUuidElem && state.selectedPersonUuid) {
      this.personUuidElem.textContent = truncateUuid(state.selectedPersonUuid);
      this.personUuidElem.setAttribute("title", state.selectedPersonUuid);
    }

    const isActive = state.currentView === "edit-person";

    setHidden(this.personTableRoot, !isActive);
    setHidden(this.referentTableRoot, !isActive);
    // controllers visibility is managed by updateChangeControllersVisibility which is
    // called when the person table data actually changes (Tabulator events or programmatic updates)
    if (!isActive) {
      setHidden(this.personTableChangeControllers, true);
    }

    if (!this.personTableRoot || !window.Tabulator) {
      return;
    }

    if (!isActive) {
      return;
    }

    // Create or update the tables with the current state data

    if (!this.tables.referent) {
      this.tables.referent = new window.Tabulator(this.referentTableRoot, {
        data: state.pendingAdds ?? [],
        columns: REFERENT_TABLE_COLUMNS,
        layout: "fitDataStretch",
        height: "600px",
      });
      this.tables.referent.off("cellClick", this.handleReferentAddClick);
      this.tables.referent.on("cellClick", this.handleReferentAddClick);
    } else {
      this.tables.referent.setData(state.pendingAdds ?? []);
    }

    /* NOT WORKING FOR SOME REASON
    this.tables.referent.on("tableBuilt", function() {
      console.log("Table built, setting sort", this.setSort);
      this.setSort("displayName", "asc");
    }); */
    
    if (!this.tables.person) {
      console.log("*** Creating person table with initial data", state.personData);
      this.tables.person = new window.Tabulator(this.personTableRoot, {
        data: (state.personData ?? []).map((row) => ({
          ...row,
          membershipStatus: row.membershipStatus ?? "existing",
        })),
        columns: PERSON_TABLE_COLUMNS,
        layout: "fitDataStretch",
      });
      this.tables.person.off("cellClick", this.handlePersonMembershipClick);
      this.tables.person.on("cellClick", this.handlePersonMembershipClick);

      // watch for table data changes so we can show/hide the save/cancel controllers
      if (typeof this.tables.person.on === "function") {
        // Tabulator: dataChanged is fired when the table data is modified
        this.tables.person.on("dataChanged", () => this.notifyPersonDataChanged());
        // additional events: rowAdded/rowDeleted/cellEdited can also change membership state
        this.tables.person.on("rowAdded", () => this.notifyPersonDataChanged());
        this.tables.person.on("rowDeleted", () => this.notifyPersonDataChanged());
        this.tables.person.on("cellEdited", () => this.notifyPersonDataChanged());
      }

      // initial visibility based on initial table data
      this.notifyPersonDataChanged();
    } else {
      console.log("*** Updating person table data with", state.personData);
      this.tables.person.setData(
        (state.personData ?? []).map((row) => ({
          ...row,
          membershipStatus: row.membershipStatus ?? "existing",
        })),
      );
      // update state and controllers after programmatic setData
      this.notifyPersonDataChanged();
    }

  }

  updateChangeControllersVisibility() {

    // lazy-resolve the controller element in case DOM wasn't present at construction time
    if (!this.personTableChangeControllers) {
      // prefer direct document lookup to avoid any scoping surprises
      this.personTableChangeControllers = document.querySelector(`#${SELECTOR_IDS.PERSON_TABLE_CHANGE_CONTROLLERS}`);
    }

    // Determine whether any rows in the person table are marked added/removed
    if (!this.personTableChangeControllers) {
      return;
    }

    const personTable = this.tables.person;
    let rows = [];

    if (personTable && typeof personTable.getData === "function") {
      rows = personTable.getData() ?? [];
    }

    const hasPending = rows.some(
      (r) => (r?.membershipStatus ?? "existing") === "added" || (r?.membershipStatus ?? "existing") === "removed",
    );
    // record that the function ran (useful for runtime checks in tests/dev)
    try { this._lastChangeControllerUpdate = { when: Date.now(), hasPending }; } catch (e) {}
    setHidden(this.personTableChangeControllers, !hasPending);
  }

  getTableOptions(kind = "person") {
    const optionsByKind = {
      person: {
        data: [],
        columns: PERSON_TABLE_COLUMNS,
      },
    };

    return optionsByKind[kind] ?? optionsByKind.person;
  }
}
