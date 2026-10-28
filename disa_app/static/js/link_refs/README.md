# Link Refs mini-application

This directory contains the client-side application that manages person/referent linkage for the Link Refs workflow. The application is deliberately small and clear: it separates state, view rendering, and API access so the save flow remains predictable and testable.

## Purpose

The application lets a user:

- select an existing person,
- review the referents already linked to that person,
- add referents from the remaining pool,
- remove referents from the current person,
- save the resulting person membership changes to the Django API.

The data model is organized around a single selected person. All pending changes are expressed in terms of that person’s referents.

## Architectural model

The application uses a simple layered design:

1. State layer
2. View layer
3. API layer
4. Testing layer

This separation keeps the UI logic from mixing directly with the database contract.

## State layer

The state is defined in `state.js` and is the source of truth for the current UI session.

Key properties include:

- `currentView`: which screen is active
- `selectedPersonUuid`: the currently selected person
- `peopleData`: the normalized list of all people and their linked referents
- `personData`: the subset of `peopleData` for the selected person
- `referentData`: the pool of available referents not already linked
- `pendingAdds`: referents queued for insertion into the selected person
- `pendingRemoves`: referents queued for removal from the selected person
- `notes`: free-text researcher note for the save operation
- `isLoading` and `error`: request status tracking

The app intentionally keeps the state object as the authoritative source for the current view. The Tabulator tables are rendered from state, not the other way around.

## View layer

The view code lives under `views/` and is responsible for rendering the visible tables and handling user actions.

The main view is `PersonEditorView` in `views/personEditorView.js`. It owns the Tabulator instances for the person table and the helper tables used for add/remove operations.

This view does three things:

- renders the selected person’s membership data,
- converts user interactions into row-level changes such as `added` or `removed`,
- reports table changes back to the application state so the save routine sees the real current data.

This pattern is important. The table is a UI projection of the state, and when the user edits the table, the corresponding state must be updated before save logic runs.

## Application shell

The `LinkRefsApp` in `app.js` is the orchestration layer. It:

- binds user actions from the view layer,
- updates state transitions,
- loads initial API data,
- invokes the save workflow,
- refreshes the screen after changes are accepted.

This is the controller for the mini-application.

## API layer

The API code is in `api/personApi.js`.

This layer is responsible for:

- normalizing UUID strings,
- building the payload expected by Django,
- sending POST requests with CSRF headers,
- calling the correct backend endpoints.

The two backend endpoints used by the app are:

- `/data/person/link-referents/`
- `/data/person/unlink-referent/`

The payload builder creates the Django-compatible fields used by the server, including:

- `person_uuid`
- `referent_uuids`
- `referent_uuid`
- `researcher_note`
- `notes`

The API layer keeps JavaScript data formatting separate from the user interface logic. This reduces the chance of inconsistent UUID handling or payload mistakes.

## Data flow

The typical flow is:

1. `boot()` loads all people and referent data from the backend.
1. `selectPersonAndOpenEditor(...)` filters the loaded data to the current person.
1. `PersonEditorView.render(...)` displays that person data in Tabulator.
1. User adds or removes referents by changing row membership status.
1. The view reports the updated row set back to application state.
1. `onSaveChanges` reads the current table rows, builds a payload, and passes it to the API layer.
1. The backend processes the link/unlink operations and returns the updated state.
1. The app reloads the people/referent data and re-renders the selected person.

This is the key architectural guarantee: the save operation reads the current table state, not stale state from before user edits.

## Utility and formatting helpers

The `utils/` directory contains reusable helpers for UUID normalization and DOM access:

- `uuid.js`: canonical UUID formatting helpers
- `dom.js`: DOM lookup
- `csrf.js`: CSRF cookie access

These helpers are intentionally small and deterministic so they can be tested independently.

## Testing model

The tests live in `tests/` and are structured around the same layers as the application.

The browser test page in `tests/index.html` executes the suite. The tests verify:

- state transitions,
- UUID normalization,
- data flattening and grouping,
- API payload generation,
- save endpoint selection,
- table-to-state synchronization.

This makes the application easier to extend safely. When a change modifies the data model or API contract, the relevant test should be updated in the same change set.

## Summary

The `link_refs` mini-application is a small, state-driven front-end for managing person linkage. Its design is intentionally straightforward:

- state is the source of truth,
- views render and react to state,
- APIs send the final payload,
- tests protect the contract between UI state and backend behavior.

This makes the workflow easier to reason about and easier to change without breaking the person linkage logic.
