import { qs } from "../utils/dom.js";
import { SELECTOR_IDS } from "../constants.js";
import { PERSON_SELECTOR_COLUMNS } from "../tables/index.js";

export class PersonSelectorView {
  constructor() {
    this.root = qs(`#${SELECTOR_IDS.EXISTING_PEOPLE_TABLE}`);
    this.table = null;
    this.handlers = {};
  }

  bindEvents({ onPersonSelected }) {
    this.handlers.onPersonSelected = onPersonSelected;
  }

  render(data = []) {

    if (!this.root) {
      return;
    }

    // Show only people who have more than one referent associated with the
    // BETTER: only one Referent where the Person is also their default Person

    const referentCountPerPerson = data.reduce((acc, { person_uuid }) => {
      acc[person_uuid] = (acc[person_uuid] ?? 0) + 1;
      return acc;
    }, {});

    data = data.filter(referent => referentCountPerPerson[referent.person_uuid] > 1);

    this.root.dataset.count = String(data.length);

    if (!window.Tabulator) {
      this.root.textContent = `People list (${data.length})`;
      return;
    }

    if (!this.root.dataset.personSelectorBound) {
      this.root.addEventListener("click", (event) => {
        const button = event.target?.closest?.(".person-select-button");
        if (!button) {
          return;
        }

        const personUuid = button.dataset.personUuid;
        if (personUuid) {
          this.handlers.onPersonSelected?.(personUuid);
        }
      });
      this.root.dataset.personSelectorBound = "true";
    }

    if (this.table) {
      this.table.setData(data);
      return;
    }

    const tableOptions = {
      data,
      columns: PERSON_SELECTOR_COLUMNS,
      groupBy: "person_uuid",
      groupStartOpen: false,
      layout: "fitDataStretch",
      groupHeader: (value, count, groupData) => {
        const personUuid = value || groupData?.[0]?.person_uuid;

        const names = groupData.map((ref) => ref.name),
          uniqueNames = Array.from(new Set(names)),
          displayedNames = uniqueNames.slice(0, 3).join(" / ");

        return `
            <button type="button" class="btn btn-sm btn-secondary person-select-button" data-person-uuid="${personUuid}">Select</button>
            <span><abbr title="${personUuid}">${personUuid.slice(0, 5)}</abbr> ${displayedNames}</span>
        `;
      },
    };

    this.table = new window.Tabulator(this.root, tableOptions);
  }

  setTable(table) {
    this.table = table;
  }

  getTableOptions(data = []) {
    return {
      data,
      columns: PERSON_SELECTOR_COLUMNS,
      groupBy: "person_uuid",
      groupStartOpen: false,
      layout: "fitDataStretch",
    };
  }
}
