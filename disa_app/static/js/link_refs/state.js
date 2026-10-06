import { DEFAULT_STATE, VIEW_KEYS } from "./constants.js";
import { formatUuid } from "./utils/uuid.js";


/*

  These functions are used to change the application state in a 
  functional programming style. The state is represented as a plain JavaScript object,
  and stored in the `LinkRefsApp` class.

  These functions ONLY operate on the state object, and do not 
  manipulate the DOM or any other part of the application.
  
  Each function takes the current state and returns a new state object with 
  the desired changes, without mutating the original state.

*/

function buildPersonData(rows = [], personUuid) {
  const normalizedPersonUuid = formatUuid(personUuid);

  return (rows ?? [])
    .filter((row) => formatUuid(row.person_uuid) === normalizedPersonUuid)
    .map((row) => ({
      ...row,
      person_uuid: formatUuid(row.person_uuid),
      referent_uuid: formatUuid(row.referent_uuid),
      displayName: row.displayName ?? row.name ?? "[Name once known]",
    }));
}

function buildAvailableReferents(referentData = [], personData = []) {
  const personReferentUuids = new Set(
    personData.map((row) => formatUuid(row.referent_uuid)).filter(Boolean),
  );

  return (referentData ?? [])
    .filter((row) => !personReferentUuids.has(formatUuid(row.referent_uuid)))
    .map((row) => ({
      ...row,
      referent_uuid: formatUuid(row.referent_uuid),
      displayName: row.displayName ?? row.name ?? "[Name once known]",
    }));
}

export function createInitialState(overrides = {}) {
  return {
    ...DEFAULT_STATE,
    ...overrides,
  };
}

export function setCurrentView(currentState, nextView) {
  const allowedViews = Object.values(VIEW_KEYS);

  if (!allowedViews.includes(nextView)) {
    throw new Error(`Unsupported view: ${nextView}`);
  }

  return {
    ...currentState,
    currentView: nextView,
    error: null,
  };
}

export function setSelectedPerson(currentState, personUuid) {
  return {
    ...currentState,
    selectedPersonUuid: personUuid,
    pendingAdds: [],
    pendingRemoves: [],
    notes: "",
  };
}

export function setPersonData(currentState, personData) {
  return {
    ...currentState,
    personData,
  };
}

export function setReferentData(currentState, referentData) {
  return {
    ...currentState,
    referentData,
  };
}

export function updatePendingAdds(currentState, pendingAdds) {
  return {
    ...currentState,
    pendingAdds,
  };
}

export function updatePendingRemoves(currentState, pendingRemoves) {
  return {
    ...currentState,
    pendingRemoves,
  };
}

export function setLoading(currentState, isLoading) {
  return {
    ...currentState,
    isLoading,
  };
}

export function setError(currentState, error) {
  return {
    ...currentState,
    error,
  };
}

export function resetToActionView(currentState) {
  return setCurrentView(currentState, VIEW_KEYS.SELECT_ACTION);
}

export function selectPersonAndOpenEditor(currentState, personUuid) {

  let personData, normalizedPersonUuid;

  if (personUuid) {
    normalizedPersonUuid = formatUuid(personUuid);
    personData = buildPersonData(currentState.peopleData ?? [], normalizedPersonUuid);
  } else {
    normalizedPersonUuid = null;
    personData = [];
  }

  const pendingAdds = buildAvailableReferents(currentState.referentData ?? [], personData);

  const withSelection = setSelectedPerson(currentState, normalizedPersonUuid);
  const withEditorData = {
    ...withSelection,
    personData,
    pendingAdds,
    pendingRemoves: [],
    notes: "",
  };

  console.log("selectPersonAndOpenEditor() - new state:", withEditorData);

  return setCurrentView(withEditorData, VIEW_KEYS.EDIT_PERSON);
}

export function loadInitialData(currentState, { peopleData, referentData }) {
  return {
    ...currentState,
    peopleData,
    referentData,
    isLoading: false,
    error: null,
  };
}
