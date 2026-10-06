import { API_ENDPOINTS } from "../constants.js";
import { formatUuid } from "../utils/uuid.js";
import { displayName } from "../utils/formatting.js";

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Request failed for ${url}: ${response.status} - ${errorText}`);
  }

  return response.json();
}

export async function loadReferentData() {
  const payload = await fetchJson(API_ENDPOINTS.REFERENT_LIST, {
    credentials: "same-origin",
  });

  const referentList = payload.referent_list ?? [];

  return referentList.map((item) => ({
    ...item,
    referent_uuid: formatUuid(item.referent_uuid),
    displayName: displayName(item),
  }));
}

export function normalizePeopleGroups(people) {
  return people.flatMap(({ person_uuid, referents = [] }) =>
    referents.map(({ referent_uuid, name }) => ({
      person_uuid: formatUuid(person_uuid),
      referent_uuid: formatUuid(referent_uuid),
      name,
    })),
  );
}

export function normalizeReferentRecord(referent) {
  if (!referent) {
    return referent;
  }

  return {
    ...referent,
    referent_uuid: formatUuid(referent.referent_uuid),
    displayName: displayName(referent),
  };
}

export function extractReferentUuidList(data = []) {
  return data
    .map((row) => row.referent_uuid)
    .filter(Boolean)
    .map((value) => formatUuid(value));
}
