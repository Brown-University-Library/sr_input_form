export const VIEW_KEYS = Object.freeze({
  SELECT_ACTION: "select-action",
  SELECT_PERSON: "select-person",
  EDIT_PERSON: "edit-person",
  CREATE_PERSON: "create-person",
});

export const SELECTOR_IDS = Object.freeze({
  CREATE_NEW_PERSON_BUTTON: "create-new-person",
  SELECT_EXISTING_PERSON_BUTTON: "select-existing-person",
  EXISTING_PEOPLE_TABLE: "existing-people-table",
  PERSON_TABLE: "person-table",
  PERSON_TABLE_CHANGE_CONTROLLERS: "person-table-change-controllers",
  REFERENT_TABLE: "referent-table",
  PERSON_ADD_TABLE: "person-add-table",
  PERSON_REMOVE_TABLE: "person-remove-table",
  PERSON_UUID: "person-uuid",
  SUBMIT_PERSON_CHANGES: "submit-person-changes",
  CANCEL_PERSON_CHANGES: "cancel-person-changes",
  SAVE_STATUS_MESSAGE: "save-status-message",
  CHANGE_PERSON_BUTTON: "change-person",
  CREATE_NEW_PERSON_BUTTON_EDIT_VIEW: "new-person-edit-view",
});

export const API_ENDPOINTS = Object.freeze({
  PEOPLE_LIST: "/data/person/all/",
  REFERENT_LIST: "/browse.json",
  SAVE_PERSON_CHANGES: "/data/person/link-referents/",
  UNLINK_PERSON_REFERENT: "/data/person/unlink-referent/",
  PERSON_CREATE: "/data/person/create/",
});

export const DEFAULT_STATE = Object.freeze({
  currentView: VIEW_KEYS.SELECT_ACTION,
  selectedPersonUuid: null,
  personData: null,
  referentData: [],
  pendingAdds: [],
  pendingRemoves: [],
  notes: "",
  isLoading: false,
  error: null,
});
