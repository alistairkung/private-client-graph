import { useState } from "react";
import { csrfHeaders } from "../../shared/csrf";

export function SignOut() {
  const [error, setError] = useState(false);
  const [pending, setPending] = useState(false);
  async function signOut() {
    setPending(true);
    setError(false);
    try {
      const response = await fetch("/auth/logout", {
        method: "POST", headers: csrfHeaders(),
      });
      if (!response.ok) throw new Error("Sign out failed");
      window.location.assign("/");
    } catch {
      setError(true);
      setPending(false);
    }
  }
  return <div className="sign-out">
    <button type="button" onClick={signOut} disabled={pending}>{pending ? "Signing out…" : "Sign out"}</button>
    {error && <span role="alert">Could not sign out. Please try again.</span>}
  </div>;
}
