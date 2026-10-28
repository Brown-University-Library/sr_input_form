export function qs(selector, root = document) {
  return root.querySelector(selector);
}

export function qsa(selector, root = document) {
  return [...root.querySelectorAll(selector)];
}

export function setHidden(element, isHidden) {
  if (!element) {
    return;
  }

  element.hidden = Boolean(isHidden);
  if (Boolean(isHidden) === false && element.style.display === "none") {
    element.style.display = "";
  }
}
