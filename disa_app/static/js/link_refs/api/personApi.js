import { API_ENDPOINTS } from "../constants.js";
import { formatUuid } from "../utils/uuid.js";
import { getCsrfToken } from "../utils/csrf.js";

async function fetchJson(url, options = {}) {
  console.log(`CALLING ${url} WITH OPTIONS:`, options);
  const response = await fetch(url, options);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `Request failed for ${url}: ${response.status} - ${errorText}`,
    );
  }

  return response.json();
}

function normalizePerson(person) {
  if (!person) {
    return person;
  }

  return {
    ...person,
    person_uuid: formatUuid(person.person_uuid),
    referents: (person.referents ?? []).map((referent) => ({
      ...referent,
      referent_uuid: formatUuid(referent.referent_uuid),
    })),
  };
}

function normalizeUuidList(values = []) {
  return (Array.isArray(values) ? values : [])
    .map((value) => formatUuid(value))
    .filter(Boolean);
}

function buildRequestOptions(body) {
  console.log("buildRequestOptions", body);
  const headers = {
    "Content-Type": "application/json",
  };

  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers["X-CSRFToken"] = csrfToken;
  }

  return {
    method: "POST",
    credentials: "same-origin",
    headers,
    body: JSON.stringify(body),
  };
}

export async function getPeopleList() {
  const payload = await fetchJson(API_ENDPOINTS.PEOPLE_LIST, {
    credentials: "same-origin",
  });

  return (payload.people ?? []).map(normalizePerson);
}

export async function getPersonByUuid(personUuid) {
  const people = await getPeopleList();
  const normalizedUuid = formatUuid(personUuid);
  return people.find((person) => person.person_uuid === normalizedUuid) ?? null;
}

// Create a new Person with an optional researcher note
// Returns the newly created Person object with its UUID and other details

async function createPerson(researcherNote = "") {
  const payload = {
    researcher_note: researcherNote,
  };
  const response = await fetchJson(API_ENDPOINTS.PERSON_CREATE, buildRequestOptions(payload));
  return normalizePerson(response);
}

export function createPersonChangePayload({
  selectedPersonUuid,
  addReferents = [],
  removeReferents = [],
  notes = "",
}) {
  const normalizedAdd = normalizeUuidList(addReferents);
  const normalizedRemove = normalizeUuidList(removeReferents);

  return {
    person_uuid: selectedPersonUuid ? formatUuid(selectedPersonUuid) : null,
    add_referents: normalizedAdd,
    remove_referents: normalizedRemove,
    referent_uuids: normalizedAdd,
    referent_uuid: normalizedRemove.length === 1 ? normalizedRemove[0] : null,
    notes,
    researcher_note: notes,
  };
}

const removeDashesFromUuid = (x) =>
  typeof x === "string" ? x.replaceAll("-", "") : null; // TEMP
const removeDashesFromUuids = (x) => x.map(removeDashesFromUuid); // TEMP

export async function savePersonChanges(payload = {}) {
  console.log("savePersonChanges XXX", payload);
  const addReferents = removeDashesFromUuids(payload.addReferents ?? []),
    removeReferents = removeDashesFromUuids(payload.removeReferents ?? []),
    linkTargetReferentUuid = removeDashesFromUuid(payload.linkTargetReferent?.referent_uuid ?? null),
    researcherNote = payload.notes ?? "",
    responses = [];

  let personUuid = payload.selectedPersonUuid ?? null;

  // Call API to create a new Person if no personUuid is provided
  if (!personUuid) {
    const newPerson = await createPerson(researcherNote);
    personUuid = newPerson.person_uuid;
    console.log("Created new person:", newPerson);
  }

  // Call API to add Referents
  console.log("DRAMA 0", {
    addReferents,
    removeReferents,
    linkTargetReferent: linkTargetReferentUuid,
    researcherNote,
    personUuid,
  });
  if (addReferents.length > 0) {
    console.log("DRAMA 1");
    addReferents.forEach(async (referentUuid) => {
      console.log("DRAMA 2");
      const response = await fetchJson(
        // API_ENDPOINTS.SAVE_PERSON_CHANGES,
        `/data/person/${personUuid}/link-referents/`,
        buildRequestOptions({
          // referent_uuid_1: str, referent_uuid_2: str, by_value: str, note: str
          //referent_uuid_1: linkTargetReferent,
          //referent_uuid_2: referentUuid,
          referent_uuid: referentUuid, // TODO: submit multiples
          by_value: "TBD",
          note: "note coming soon",
        }),
      );
      console.log("DRAMA 2 RESPONSE", response);
      responses.push(response);
    });

    /*
    const response = await fetchJson(
      API_ENDPOINTS.SAVE_PERSON_CHANGES,
      buildRequestOptions({
        // referent_uuid_1: str, referent_uuid_2: str, by_value: str, note: str
        referent_uuid_1: linkTargetReferent,
        referent_uuid_2: 
        //person_uuid: personUuid,
        //referent_uuids: addReferents,
        //researcher_note: researcherNote,
      }),
    );
    responses.push(response);*/
  }

  // Call API to remove Referents

  for (const referentUuid of removeReferents) {
    const response = await fetchJson(
      API_ENDPOINTS.UNLINK_PERSON_REFERENT,
      buildRequestOptions({
        // referent_uuid: str, by_value: str, note: str
        referent_uuid: referentUuid,
        note: researcherNote,
        // person_uuid: personUuid,
        // referent_uuid: referentUuid,
        // researcher_note: researcherNote,
      }),
    );
    responses.push(response);
  }

  return responses.length > 0 ? responses[responses.length - 1] : { ok: true };
}
