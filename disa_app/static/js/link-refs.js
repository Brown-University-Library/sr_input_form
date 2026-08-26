import { initializeTabulatorTables } from "./link-refs_initializeTabulator.js";

// Global variables

const STATE_CLASS_NAMES = [
  "state-edit-person",
  "state-create-person",
  "state-select-person",
  "state-select-action",
];

const selector = STATE_CLASS_NAMES.map((cn) => `.${cn}`).join(", "),
  STATE_DOM_ELEMS = document.querySelectorAll(selector);

// Initialize states

function initializeEditPersonState() {}

function initializeCreatePersonState() {}

function initializeSelectPersonState() {}

function initializeSelectActionState() {
  // Click handlers for buttons

  document.getElementById("create-new-person").addEventListener("click", () => {
    changeStateToCreatePerson();
  });

  document
    .getElementById("select-existing-person")
    .addEventListener("click", () => {
      changeStateToSelectPerson();
    });
}

// Change states

function updateVisibilityForState(currentStateClassName) {
  STATE_DOM_ELEMS.forEach((el) => {
    el.style.display = el.classList.contains(currentStateClassName)
      ? ""
      : "none";
  });
}

function changeStateToEditPerson() {
  updateVisibilityForState("state-edit-person");
}

function changeStateToCreatePerson(referentUuid) {
  updateVisibilityForState("state-create-person");
  // Optional parameter referentUuid can be used to pre-fill the form with data from the referent
}

function changeStateToSelectAction() {
  updateVisibilityForState("state-select-action");
}

function changeStateToSelectPerson() {
  updateVisibilityForState("state-select-person");
  // Change the state of the application to select a person to seed the edit-person state
}

// Main setup area

function parseUrlForInitialState() {
  // Parse the URL to determine the current state of the application
  // This could involve checking the path or query parameters to determine what action to take
  const urlParams = new URLSearchParams(window.location.search),
    referentUuid = urlParams.get("referent_uuid"),
    personUuid = urlParams.get("person_uuid");

  if (referentUuid) {
    // If a UUID is present in the URL, we can assume we're editing an existing person
    const personUuid = getPersonUuidFromReferentUuid(referentUuid);
    if (personUuid) {
      changeStateToEditPerson(personUuid);
    } else {
      // If no person UUID is found for the referent UUID, we can assume we're creating a new person
      changeStateToCreatePerson(referentUuid);
    }
  } else if (personUuid) {
    // If no referent UUID is present but a person UUID is, we can assume we're editing an existing person
    changeStateToEditPerson(personUuid);
  } else {
    // Default: offer action options to user
    changeStateToSelectAction();
  }
}

function initializeStates() {
  initializeEditPersonState();
  initializeCreatePersonState();
  initializeSelectPersonState();
  initializeSelectActionState();
}

function main() {
  initializeStates();
  initializeTabulatorTables();
  parseUrlForInitialState();
}

main();
