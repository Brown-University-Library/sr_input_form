const tests = [];

export function test(name, fn) {
  tests.push({ name, fn });
}

export function runTests() {
  const resultsEl = document.getElementById("results");
  const summaryEl = document.getElementById("summary");
  const failures = [];

  if (!resultsEl || !summaryEl) {
    throw new Error("Test page must include #results and #summary elements.");
  }

  tests.forEach(({ name, fn }) => {
    const row = document.createElement("div");
    row.className = "test-row";

    try {
      fn();
      row.textContent = `PASS: ${name}`;
      row.classList.add("pass");
    } catch (error) {
      failures.push({ name, error });
      row.textContent = `FAIL: ${name} — ${error.message}`;
      row.classList.add("fail");
    }

    resultsEl.appendChild(row);
  });

  const passed = tests.length - failures.length;
  summaryEl.textContent = `Passed ${passed} / ${tests.length} tests`;
  summaryEl.classList.toggle("fail", failures.length > 0);

  if (failures.length > 0) {
    console.error("Link refs test failures:", failures);
  }
}

export function assertEqual(actual, expected, message = "") {
  if (actual !== expected) {
    throw new Error(`${message || "Assertion failed"}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

export function assertDeepEqual(actual, expected, message = "") {
  const normalizedActual = JSON.stringify(actual);
  const normalizedExpected = JSON.stringify(expected);

  if (normalizedActual !== normalizedExpected) {
    throw new Error(`${message || "Deep equality assertion failed"}: expected ${normalizedExpected}, got ${normalizedActual}`);
  }
}

export function assert(condition, message = "Assertion failed") {
  if (!condition) {
    throw new Error(message);
  }
}

export function resetTests() {
  tests.length = 0;
}

export async function withMockFetch(mockImplementation, callback) {
  const originalFetch = window.fetch;
  window.fetch = mockImplementation;

  try {
    return await callback();
  } finally {
    window.fetch = originalFetch;
  }
}
