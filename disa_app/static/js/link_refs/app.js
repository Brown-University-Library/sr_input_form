import { VIEW_KEYS } from "./constants.js";
import {
  createInitialState,
  loadInitialData,
  selectPersonAndOpenEditor,
  setCurrentView,
  setError,
  setLoading,
} from "./state.js";
import { ActionChooserView } from "./views/actionChooserView.js";
import { PersonSelectorView } from "./views/personSelectorView.js";
import { PersonEditorView } from "./views/personEditorView.js";
import {
  createPersonChangePayload,
  getPeopleList,
  getPersonByUuid,
  savePersonChanges,
} from "./api/personApi.js";
import { loadReferentData, normalizePeopleGroups } from "./api/referentApi.js";

export class LinkRefsApp {
  constructor({ rootDocument = document } = {}) {
    this.document = rootDocument;
    this.state = createInitialState();

    this.views = {
      actionChooser: new ActionChooserView(),
      personSelector: new PersonSelectorView(),
      personEditor: new PersonEditorView(),
    };
  }

  bindEvents() {
    this.views.actionChooser.bindEvents({
      // onCreateNewPerson: () => this.goTo(VIEW_KEYS.CREATE_PERSON),
      onCreateNewPerson: () => {
        const personUuid = null; // New person has no UUID yet
        this.state = selectPersonAndOpenEditor(this.state, personUuid);
        this.goTo(VIEW_KEYS.EDIT_PERSON);
        this.render();
      },
      onSelectExistingPerson: () => this.goTo(VIEW_KEYS.SELECT_PERSON),
    });

    this.views.personSelector.bindEvents({
      onPersonSelected: (personUuid) => {
        this.state = selectPersonAndOpenEditor(this.state, personUuid);
        this.goTo(VIEW_KEYS.EDIT_PERSON);
        this.render();
      },
    });

    this.views.personEditor.bindEvents({

      // Called when user clicks "Change Person" button in the Person Editor view

      onChangePerson: () => {
        // alert("YES - Change Person button clicked");
        this.goTo(VIEW_KEYS.SELECT_PERSON);
      },

      onPersonDataChanged: (rows = []) => {
        this.state = {
          ...this.state,
          personData: (rows ?? []).map((row) => ({
            ...row,
            membershipStatus: row.membershipStatus ?? "existing",
          })),
        };
      },

      // Called when user clicks "Save Changes" button in the Person Editor view

      onSaveChanges: async () => {

        // Create payload for saving person changes

        const personRows =
          this.views.personEditor.tables.person?.getData?.() ??
          this.state.personData ??
          [];
        const referentsToAdd = personRows
          .filter((row) => (row.membershipStatus ?? "existing") === "added")
          .map((row) => row.referent_uuid)
          .filter(Boolean);
        const referentsToRemove = personRows
          .filter((row) => (row.membershipStatus ?? "existing") === "removed")
          .map((row) => row.referent_uuid)
          .filter(Boolean);
        const linkTargetReferent =
          personRows.find((row) => row.membershipStatus === "existing") ??
          referentsToRemove[0];
        if (referentsToAdd.length === 0 && referentsToRemove.length === 0) {
          return;
        }

        const payload = {
          selectedPersonUuid: this.state.selectedPersonUuid,
          addReferents: referentsToAdd,
          removeReferents: referentsToRemove,
          linkTargetReferent,
          notes: this.state.notes ?? "",
        }

        console.log("Payload for saving person changes:", payload);

        // Set loading state ("Loading ...")

        this.state = setLoading(this.state, true);
        this.render();

        // Submit payload to API and handle response

        try {
          await savePersonChanges(payload);

          // Refresh data and re-render the app
          // (Apparently need to wait a bit to ensure the backend has processed 
          // the changes before fetching updated data - this seems kludgy)

          const WAIT_TIME_MS = 2000; // Wait time for backend (mySQL?)

          setTimeout(async () => {
            const [people, referents] = await Promise.all([
              getPeopleList(),
              loadReferentData(),
            ]);

            const peopleData = normalizePeopleGroups(people);

            this.state = loadInitialData(this.state, {
              peopleData,
              referentData: referents,
            });

            this.state = selectPersonAndOpenEditor(
              this.state,
              this.state.selectedPersonUuid,
            );

            this.render();
          }, WAIT_TIME_MS);

        } catch (error) {
          this.state = setError(this.state, error);
          console.error(error);
        } finally {
          this.state = setLoading(this.state, false);
          this.render();
        }
      },

      // Called when user clicks "Cancel" button in the Person Editor view

      onCancelChanges: () => {
        this.state = selectPersonAndOpenEditor(
          this.state,
          this.state.selectedPersonUuid,
        );
        this.render();
      },
    });
  }

  async boot() {
    this.bindEvents();
    this.state = setLoading(this.state, true);
    this.render();

    try {
      const [people, referents] = await Promise.all([
        getPeopleList(),
        loadReferentData(),
      ]);

      const peopleData = normalizePeopleGroups(people);
      this.state = loadInitialData(this.state, {
        peopleData,
        referentData: referents,
      });

      this.render();
    } catch (error) {
      this.state = setError(this.state, error);
      console.error(error);
      this.render();
    } finally {
      this.state = setLoading(this.state, false);
      this.render();
    }
  }

  goTo(viewName) {
    this.state = setCurrentView(this.state, viewName);
    console.log("Navigating to view:", viewName);

    // update URL to include current view (e.g., ?view=select-person)
    const url = new URL(window.location);
    url.searchParams.set("view", viewName);
    window.history.replaceState({}, "", url);

    this.render();
  }

  render() {
    console.log("Rendering app with state:", this.state);
    this.views.actionChooser.render(this.state);
    this.views.personSelector.render(this.state.peopleData ?? []);
    this.views.personEditor.render(this.state);
    this.renderViewVisibility();
  }

  renderViewVisibility() {
    const view = this.state.currentView;
    const selectors = {
      [VIEW_KEYS.SELECT_ACTION]: ".state-select-action",
      [VIEW_KEYS.SELECT_PERSON]: ".state-select-person",
      [VIEW_KEYS.EDIT_PERSON]: ".state-edit-person",
      [VIEW_KEYS.CREATE_PERSON]: ".state-create-person",
    };

    Object.entries(selectors).forEach(([key, selector]) => {
      const element = this.document.querySelector(selector);
      if (!element) {
        return;
      }
      element.hidden = key !== view;
    });
  }
}

export function createLinkRefsApp(options = {}) {
  return new LinkRefsApp(options);
}
