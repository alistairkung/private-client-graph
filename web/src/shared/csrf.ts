export function csrfHeaders(): Record<string, string> {
  const csrf = document.cookie.split("; ").find(value => value.startsWith("__Host-pcg-csrf="))?.split("=")[1] ?? "";
  return { "x-csrftoken": csrf };
}
