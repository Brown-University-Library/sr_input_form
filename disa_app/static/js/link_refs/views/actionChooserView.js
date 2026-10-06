import { qs } from "../utils/dom.js";
import { SELECTOR_IDS } from "../constants.js";

export class ActionChooserView {
  constructor() {
    this.createButton = qs(`#${SELECTOR_IDS.CREATE_NEW_PERSON_BUTTON}`);
    this.selectButton = qs(`#${SELECTOR_IDS.SELECT_EXISTING_PERSON_BUTTON}`);
    this.handlers = {};
  }

  bindEvents({ onCreateNewPerson, onSelectExistingPerson }) {
    this.handlers.onCreateNewPerson = onCreateNewPerson;
    this.handlers.onSelectExistingPerson = onSelectExistingPerson;

    if (this.createButton) {
      this.createButton.addEventListener("click", () => {
        this.handlers.onCreateNewPerson?.();
      });
    }

    if (this.selectButton) {
      this.selectButton.addEventListener("click", () => {
        this.handlers.onSelectExistingPerson?.();
      });
    }
  }

  render(state) {
    // View rendering can be handled centrally by the app shell.
    return state;
  }
}
