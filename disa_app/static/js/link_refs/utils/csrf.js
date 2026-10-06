
export function getCsrfToken() {
  const cookieString = document.cookie || "";

  if (!cookieString) {
    return "";
  }

  const csrfCookie = cookieString
    .split(";")
    .map((cookie) => cookie.trim())
    .find((cookie) => cookie.startsWith("csrftoken="));

  if (!csrfCookie) {
    return "";
  }

  return csrfCookie.slice("csrftoken=".length) || "";
}
