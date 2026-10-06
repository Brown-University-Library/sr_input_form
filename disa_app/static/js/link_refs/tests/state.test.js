import { test, assertEqual, assertDeepEqual, assert } from "./test-runner.js";
import {
  createInitialState,
  setCurrentView,
  setSelectedPerson,
  selectPersonAndOpenEditor,
  resetToActionView,
  loadInitialData,
} from "../state.js";
import { VIEW_KEYS } from "../constants.js";

test("createInitialState applies default values", () => {
  const state = createInitialState();

  assertEqual(state.currentView, VIEW_KEYS.SELECT_ACTION);
  assertEqual(state.selectedPersonUuid, null);
  assertDeepEqual(state.pendingAdds, []);
  assertDeepEqual(state.pendingRemoves, []);
});

test("setCurrentView accepts valid state transitions", () => {
  const initial = createInitialState();
  const next = setCurrentView(initial, VIEW_KEYS.SELECT_PERSON);

  assertEqual(next.currentView, VIEW_KEYS.SELECT_PERSON);
  assertEqual(next.error, null);
});

test("setCurrentView rejects invalid view keys", () => {
  const initial = createInitialState();

  try {
    setCurrentView(initial, "not-a-view");
    throw new Error("Expected invalid view to throw");
  } catch (error) {
    assert(error.message.includes("Unsupported view"), "Expected unsupported view error");
  }
});

test("selectPersonAndOpenEditor updates selection and opens editor", () => {
  const initial = createInitialState({
    peopleData: [
      { person_uuid: "123e4567e89b12d3a456426614174000", referent_uuid: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", name: "Alpha" },
      { person_uuid: "123e4567e89b12d3a456426614174000", referent_uuid: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", name: "Bravo" },
    ],
    referentData: [
      { referent_uuid: "cccccccccccccccccccccccccccccccc", displayName: "Charlie" },
      { referent_uuid: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", displayName: "Alpha" },
      { referent_uuid: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", displayName: "Bravo" },
    ],
  });

  const next = selectPersonAndOpenEditor(initial, "123e4567-e89b-12d3-a456-426614174000");

  assertEqual(next.selectedPersonUuid, "123e4567-e89b-12d3-a456-426614174000");
  assertEqual(next.currentView, VIEW_KEYS.EDIT_PERSON);
  assertEqual(next.personData.length, 2);
  assertEqual(next.pendingAdds.length, 1);
  assertEqual(next.pendingAdds[0].referent_uuid, "cccccccc-cccc-cccc-cccc-cccccccccccc");
  assertEqual(next.pendingAdds.some((row) => row.referent_uuid === "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), false);
  assertEqual(next.pendingAdds.some((row) => row.referent_uuid === "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"), false);
});

test("resetToActionView returns to the select-action screen", () => {
  const initial = createInitialState({ currentView: VIEW_KEYS.EDIT_PERSON });
  const next = resetToActionView(initial);

  assertEqual(next.currentView, VIEW_KEYS.SELECT_ACTION);
});

test("loadInitialData merges fetched data and clears loading state", () => {
  const initial = createInitialState({ isLoading: true });
  const next = loadInitialData(initial, {
    peopleData: [{ person_uuid: "abc" }],
    referentData: [{ referent_uuid: "def" }],
  });

  assertDeepEqual(next.peopleData, [{ person_uuid: "abc" }]);
  assertDeepEqual(next.referentData, [{ referent_uuid: "def" }]);
  assertEqual(next.isLoading, false);
  assertEqual(next.error, null);
});

test("setSelectedPerson clears pending changes when selecting another person", () => {
  const initial = createInitialState({
    pendingAdds: ["a"],
    pendingRemoves: ["b"],
    notes: "old note",
  });

  const next = setSelectedPerson(initial, "person-1");

  assertEqual(next.selectedPersonUuid, "person-1");
  assertDeepEqual(next.pendingAdds, []);
  assertDeepEqual(next.pendingRemoves, []);
  assertEqual(next.notes, "");
});
