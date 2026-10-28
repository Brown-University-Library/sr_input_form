import { test, assertEqual, assertDeepEqual, withMockFetch } from "./test-runner.js";
import { createPersonChangePayload, getPeopleList, savePersonChanges } from "../api/personApi.js";
import { loadReferentData, normalizePeopleGroups, normalizeReferentRecord, extractReferentUuidList } from "../api/referentApi.js";
import { PersonEditorView } from "../views/personEditorView.js";

const peopleTableRows = [
  { uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e", researcher_notes: "Initial default Person for Referent 2a18eb5442964353b170a114b74d0f3c", resolved_person_uuid: "" },
  { uuid: "1453f11a-a186-11f1-8fd5-f6377c59bb4e", researcher_notes: "Initial default Person for Referent 2cd989acc25841e69388682ff80edde1", resolved_person_uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e" },
  { uuid: "1461dd78-a186-11f1-8fd5-f6377c59bb4e", researcher_notes: "Initial default Person for Referent 1df2754725ea471cb6f013dc4f489425", resolved_person_uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e" },
  { uuid: "33c3b1f4-a18f-11f1-8fd5-f6377c59bb4e", researcher_notes: "Initial default Person for Referent c3bd07fbfa14454d80c57dbbf5b879b7", resolved_person_uuid: "" },
  { uuid: "33c87ef3-a18f-11f1-8fd5-f6377c59bb4e", researcher_notes: "Initial default Person for Referent 1a2ba78470bf4f81a0b7bb88041b9adb", resolved_person_uuid: "33c3b1f4-a18f-11f1-8fd5-f6377c59bb4e" },
  { uuid: "33ddca51-a18f-11f1-8fd5-f6377c59bb4e", researcher_notes: "Initial default Person for Referent ad58acc0fe954bd9b09a89849bccbcd2", resolved_person_uuid: "33c3b1f4-a18f-11f1-8fd5-f6377c59bb4e" },
  { uuid: "33e7ea33-a18f-11f1-8fd5-f6377c59bb4e", researcher_notes: "Initial default Person for Referent 12c1bd236ecb4249ba14b36162545279", resolved_person_uuid: "33c3b1f4-a18f-11f1-8fd5-f6377c59bb4e" },
  { uuid: "5850edb2-a18f-11f1-8fd5-f6377c59bb4e", researcher_notes: "Initial default Person for Referent f377c053ce49435c8e22a1d20e94c20d", resolved_person_uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e" },
  { uuid: "585d467a-a18f-11f1-8fd5-f6377c59bb4e", researcher_notes: "Initial default Person for Referent e7dd4d792b874efcabc43762bc5beec0", resolved_person_uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e" },
  { uuid: "58645aa3-a18f-11f1-8fd5-f6377c59bb4e", researcher_notes: "Initial default Person for Referent f2716c46eb114b8cb4bc006e36e53b3f", resolved_person_uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e" },
];

const isPersonTableRows = [
  { uuid: "14538431-a186-11f1-8fd5-f6377c59bb4e", referent_uuid: "2a18eb5442964353b170a114b74d0f3c", person_uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e", person_uuid_default: "14534866-a186-11f1-8fd5-f6377c59bb4e", researcher_log: "init_person" },
  { uuid: "1453f451-a186-11f1-8fd5-f6377c59bb4e", referent_uuid: "2cd989acc25841e69388682ff80edde1", person_uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e", person_uuid_default: "1453f11a-a186-11f1-8fd5-f6377c59bb4e", researcher_log: "init_person; unify_referents" },
  { uuid: "1461fc41-a186-11f1-8fd5-f6377c59bb4e", referent_uuid: "1df2754725ea471cb6f013dc4f489425", person_uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e", person_uuid_default: "1461dd78-a186-11f1-8fd5-f6377c59bb4e", researcher_log: "init_person; unify_referents" },
  { uuid: "33c6a4eb-a18f-11f1-8fd5-f6377c59bb4e", referent_uuid: "c3bd07fbfa14454d80c57dbbf5b879b7", person_uuid: "33c3b1f4-a18f-11f1-8fd5-f6377c59bb4e", person_uuid_default: "33c3b1f4-a18f-11f1-8fd5-f6377c59bb4e", researcher_log: "init_person" },
  { uuid: "33c888f8-a18f-11f1-8fd5-f6377c59bb4e", referent_uuid: "1a2ba78470bf4f81a0b7bb88041b9adb", person_uuid: "33c3b1f4-a18f-11f1-8fd5-f6377c59bb4e", person_uuid_default: "33c87ef3-a18f-11f1-8fd5-f6377c59bb4e", researcher_log: "init_person; unify_referents" },
  { uuid: "33de0868-a18f-11f1-8fd5-f6377c59bb4e", referent_uuid: "ad58acc0fe954bd9b09a89849bccbcd2", person_uuid: "33c3b1f4-a18f-11f1-8fd5-f6377c59bb4e", person_uuid_default: "33ddca51-a18f-11f1-8fd5-f6377c59bb4e", researcher_log: "init_person; unify_referents" },
  { uuid: "33e833ca-a18f-11f1-8fd5-f6377c59bb4e", referent_uuid: "12c1bd236ecb4249ba14b36162545279", person_uuid: "33c3b1f4-a18f-11f1-8fd5-f6377c59bb4e", person_uuid_default: "33e7ea33-a18f-11f1-8fd5-f6377c59bb4e", researcher_log: "init_person; unify_referents" },
  { uuid: "5851a3fd-a18f-11f1-8fd5-f6377c59bb4e", referent_uuid: "f377c053ce49435c8e22a1d20e94c20d", person_uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e", person_uuid_default: "5850edb2-a18f-11f1-8fd5-f6377c59bb4e", researcher_log: "init_person; unify_referents" },
  { uuid: "585d7a6b-a18f-11f1-8fd5-f6377c59bb4e", referent_uuid: "e7dd4d792b874efcabc43762bc5beec0", person_uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e", person_uuid_default: "585d467a-a18f-11f1-8fd5-f6377c59bb4e", researcher_log: "init_person; unify_referents" },
  { uuid: "58648172-a18f-11f1-8fd5-f6377c59bb4e", referent_uuid: "f2716c46eb114b8cb4bc006e36e53b3f", person_uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e", person_uuid_default: "58645aa3-a18f-11f1-8fd5-f6377c59bb4e", researcher_log: "init_person; unify_referents" },
];

function canonicalPersonMap(rows) {
  const map = new Map();

  for (const row of rows) {
    const target = row.person_uuid || row.person_uuid_default || row.uuid;
    map.set(row.referent_uuid, target);
  }

  return map;
}

function groupByCanonicalPerson(rows) {
  const groups = new Map();
  const map = canonicalPersonMap(rows);

  for (const row of rows) {
    const personUuid = map.get(row.referent_uuid);
    const current = groups.get(personUuid) ?? [];
    current.push(row.referent_uuid);
    groups.set(personUuid, current);
  }

  return groups;
}

test("normalizePeopleGroups flattens people and referent data into selection rows", () => {
  const people = [
    {
      person_uuid: "550e8400e29b41d4a716446655440000",
      referents: [
        { referent_uuid: "6f4e9a55d1874c9db1262b61bd7b94d2", name: "Alice" },
        { referent_uuid: "c4f005f5a9bb4d36a9db7d8d3da51a00", name: "Alicia" },
      ],
    },
  ];

  const rows = normalizePeopleGroups(people);

  assertEqual(rows.length, 2);
  assertEqual(rows[0].person_uuid, "550e8400-e29b-41d4-a716-446655440000");
  assertEqual(rows[0].referent_uuid, "6f4e9a55-d187-4c9d-b126-2b61bd7b94d2");
  assertEqual(rows[0].name, "Alice");
});

test("normalizeReferentRecord formats UUID and display name", () => {
  const row = normalizeReferentRecord({
    referent_uuid: "550e8400e29b41d4a716446655440000",
    name_first: "Ada",
    name_last: "Lovelace",
  });

  assertEqual(row.referent_uuid, "550e8400-e29b-41d4-a716-446655440000");
  assertEqual(row.displayName, "Ada Lovelace");
});

test("extractReferentUuidList converts all rows to canonical UUIDs", () => {
  const rows = [
    { referent_uuid: "550e8400e29b41d4a716446655440000" },
    { referent_uuid: "550E8400-E29B-41D4-A716-446655440000" },
  ];

  assertDeepEqual(extractReferentUuidList(rows), [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440000",
  ]);
});

test("createPersonChangePayload formats all UUIDs and includes the API contract fields", () => {
  const payload = createPersonChangePayload({
    selectedPersonUuid: "550e8400e29b41d4a716446655440000",
    addReferents: ["6f4e9a55d1874c9db1262b61bd7b94d2"],
    removeReferents: ["c4f005f5a9bb4d36a9db7d8d3da51a00"],
    notes: "added and removed as part of review",
  });

  assertEqual(payload.person_uuid, "550e8400-e29b-41d4-a716-446655440000");
  assertDeepEqual(payload.add_referents, ["6f4e9a55-d187-4c9d-b126-2b61bd7b94d2"]);
  assertDeepEqual(payload.remove_referents, ["c4f005f5-a9bb-4d36-a9db-7d8d3da51a00"]);
  assertDeepEqual(payload.referent_uuids, ["6f4e9a55-d187-4c9d-b126-2b61bd7b94d2"]);
  assertEqual(payload.referent_uuid, "c4f005f5-a9bb-4d36-a9db-7d8d3da51a00");
  assertEqual(payload.notes, "added and removed as part of review");
  assertEqual(payload.researcher_note, "added and removed as part of review");
});

test("database fixture groups referents by their canonical person IDs", () => {
  const canonicalMap = canonicalPersonMap(isPersonTableRows);

  assertEqual(canonicalMap.get("2a18eb5442964353b170a114b74d0f3c"), "14534866-a186-11f1-8fd5-f6377c59bb4e");
  assertEqual(canonicalMap.get("2cd989acc25841e69388682ff80edde1"), "14534866-a186-11f1-8fd5-f6377c59bb4e");
  assertEqual(canonicalMap.get("1df2754725ea471cb6f013dc4f489425"), "14534866-a186-11f1-8fd5-f6377c59bb4e");
  assertEqual(canonicalMap.get("c3bd07fbfa14454d80c57dbbf5b879b7"), "33c3b1f4-a18f-11f1-8fd5-f6377c59bb4e");
  assertEqual(canonicalMap.get("f377c053ce49435c8e22a1d20e94c20d"), "14534866-a186-11f1-8fd5-f6377c59bb4e");
});

test("database fixture produces two canonical person groups", () => {
  const groups = groupByCanonicalPerson(isPersonTableRows);

  assertEqual(groups.size, 2);
  assertEqual(groups.get("14534866-a186-11f1-8fd5-f6377c59bb4e").length, 6);
  assertEqual(groups.get("33c3b1f4-a18f-11f1-8fd5-f6377c59bb4e").length, 4);
});

test("person table rows resolve to canonical people, preserving default-person transitions", () => {
  const resolvedPersonByUuid = new Map();

  for (const row of peopleTableRows) {
    resolvedPersonByUuid.set(row.uuid, row.resolved_person_uuid || row.uuid);
  }

  assertEqual(resolvedPersonByUuid.get("1453f11a-a186-11f1-8fd5-f6377c59bb4e"), "14534866-a186-11f1-8fd5-f6377c59bb4e");
  assertEqual(resolvedPersonByUuid.get("35c3b1f4-a18f-11f1-8fd5-f6377c59bb4e") ?? null, null);
  assertEqual(resolvedPersonByUuid.get("5850edb2-a18f-11f1-8fd5-f6377c59bb4e"), "14534866-a186-11f1-8fd5-f6377c59bb4e");
});

test("loadReferentData fetches browse data and normalizes it", async () => {
  const payload = {
    referent_list: [
      {
        referent_uuid: "2a18eb5442964353b170a114b74d0f3c",
        name_first: "Alice",
        name_last: "Jones",
      },
      {
        referent_uuid: "2cd989acc25841e69388682ff80edde1",
        name_first: "Alice",
        name_last: "",
      },
    ],
  };

  await withMockFetch(async (url, options) => ({
    ok: true,
    url,
    options,
    json: async () => payload,
    text: async () => JSON.stringify(payload),
  }), async () => {
    const data = await loadReferentData();

    assertEqual(data[0].referent_uuid, "2a18eb54-4296-4353-b170-a114b74d0f3c");
    assertEqual(data[0].displayName, "Alice Jones");
    assertEqual(data[1].referent_uuid, "2cd989ac-c258-41e6-9388-682ff80edde1");
    assertEqual(data[1].displayName, "Alice");
  });
});

test("getPeopleList fetches person data and normalizes UUIDs", async () => {
  const payload = {
    people: [
      {
        person_uuid: "14534866a18611f18fd5f6377c59bb4e",
        referents: [
          { referent_uuid: "2a18eb5442964353b170a114b74d0f3c", name: "Alice" },
        ],
      },
    ],
  };

  await withMockFetch(async (url, options) => ({
    ok: true,
    url,
    options,
    json: async () => payload,
    text: async () => JSON.stringify(payload),
  }), async () => {
    const data = await getPeopleList();

    assertEqual(data[0].person_uuid, "14534866-a186-11f1-8fd5-f6377c59bb4e");
    assertEqual(data[0].referents[0].referent_uuid, "2a18eb54-4296-4353-b170-a114b74d0f3c");
  });
});

test("PersonEditorView syncs the latest table rows back into app state", () => {
  const view = new PersonEditorView();
  let latestRows = null;

  view.bindEvents({
    onPersonDataChanged: (rows) => {
      latestRows = rows;
    },
  });

  view.tables.person = {
    getData: () => [
      { referent_uuid: "550e8400e29b41d4a716446655440000", membershipStatus: "removed" },
      { referent_uuid: "6f4e9a55d1874c9db1262b61bd7b94d2", membershipStatus: "added" },
    ],
  };

  view.notifyPersonDataChanged();

  assertEqual(latestRows.length, 2);
  assertEqual(latestRows[0].membershipStatus, "removed");
  assertEqual(latestRows[1].membershipStatus, "added");
});

test("savePersonChanges hits the link and unlink endpoints using the Django payload contract", async () => {
  const originalCookieDescriptor = Object.getOwnPropertyDescriptor(Document.prototype, "cookie") ?? Object.getOwnPropertyDescriptor(document, "cookie");
  const calls = [];

  Object.defineProperty(document, "cookie", {
    configurable: true,
    get: () => "csrftoken=abc123",
    set: () => {},
  });

  await withMockFetch(async (url, options) => {
    calls.push({ url, options, body: JSON.parse(options.body) });
    return {
      ok: true,
      url,
      options,
      json: async () => ({ ok: true, person_uuid: "14534866-a186-11f1-8fd5-f6377c59bb4e" }),
      text: async () => JSON.stringify({ ok: true }),
    };
  }, async () => {
    const payload = createPersonChangePayload({
      selectedPersonUuid: "14534866a18611f18fd5f6377c59bb4e",
      addReferents: ["2a18eb5442964353b170a114b74d0f3c"],
      removeReferents: ["2cd989acc25841e69388682ff80edde1"],
      notes: "reviewed",
    });

    const response = await savePersonChanges(payload);

    assertEqual(response.ok, true);
    assertEqual(calls.length, 2);
    assertEqual(calls[0].url, "/data/person/link-referents/");
    assertEqual(calls[0].options.method, "POST");
    assertEqual(calls[0].options.headers["X-CSRFToken"], "abc123");
    assertDeepEqual(calls[0].body.referent_uuids, ["2a18eb54-4296-4353-b170-a114b74d0f3c"]);
    assertEqual(calls[0].body.researcher_note, "reviewed");
    assertEqual(calls[1].url, "/data/person/unlink-referent/");
    assertEqual(calls[1].body.referent_uuid, "2cd989ac-c258-41e6-9388-682ff80edde1");
    assertEqual(calls[1].body.researcher_note, "reviewed");
  });

  if (originalCookieDescriptor) {
    Object.defineProperty(document, "cookie", originalCookieDescriptor);
  } else {
    delete document.cookie;
  }
});
