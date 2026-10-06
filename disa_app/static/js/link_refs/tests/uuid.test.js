import { test, assertEqual, assert } from "./test-runner.js";
import { formatUuid, unformatUuid } from "../utils/uuid.js";

test("formatUuid converts 32-char hex into canonical UUID format", () => {
  const value = "550e8400e29b41d4a716446655440000";
  const formatted = formatUuid(value);

  assertEqual(formatted, "550e8400-e29b-41d4-a716-446655440000");
});

test("formatUuid leaves already-formatted or invalid UUID values alone", () => {
  assertEqual(formatUuid("550e8400-e29b-41d4-a716-446655440000"), "550e8400-e29b-41d4-a716-446655440000");
  assertEqual(formatUuid("not-a-uuid"), "not-a-uuid");
  assertEqual(formatUuid(""), "");
});

test("unformatUuid strips hyphens and lowercases values", () => {
  const value = "550E8400-E29B-41D4-A716-446655440000";
  assertEqual(unformatUuid(value), "550e8400e29b41d4a716446655440000");
});

test("unformatUuid returns non-string values unchanged", () => {
  assertEqual(unformatUuid(null), null);
  assertEqual(unformatUuid(undefined), undefined);
});
