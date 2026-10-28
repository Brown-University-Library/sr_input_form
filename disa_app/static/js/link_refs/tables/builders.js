export function buildTableConfig(overrides = {}) {
  return {
    layout: "fitDataStretch",
    placeholder: "No data",
    ...overrides,
  };
}

export function createPersonSelectorTable(targetSelector, data, callbacks = {}) {
  const { onRowSelect } = callbacks;

  return {
    targetSelector,
    data,
    onRowSelect,
    type: "person-selector-table",
  };
}

export function createPersonEditorTables(targets, data = {}) {
  return {
    personTableTarget: targets.personTableTarget,
    addTableTarget: targets.addTableTarget,
    removeTableTarget: targets.removeTableTarget,
    personData: data.personData ?? [],
    addData: data.addData ?? [],
    removeData: data.removeData ?? [],
    type: "person-editor-tables",
  };
}
