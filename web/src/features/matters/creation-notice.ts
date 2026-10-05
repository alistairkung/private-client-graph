// A one-time navigation receipt, not persisted professional review state.
const key = "pcg-created-matter";

export function rememberMatterCreation(path: string) {
  try { sessionStorage.setItem(key, path); } catch { /* Navigation must work with storage disabled. */ }
}

export function consumeMatterCreation(id: string): boolean {
  try {
    if (sessionStorage.getItem(key) !== `/app/matters/${encodeURIComponent(id)}`) return false;
    sessionStorage.removeItem(key);
    return true;
  } catch { return false; }
}
