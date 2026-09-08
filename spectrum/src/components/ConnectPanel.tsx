"use client";

import { useState, FormEvent } from "react";

/**
 * Stub only — does NOT call ČTÚ login / access-token APIs.
 * Dry-run validates the form and shows honest “coming soon” copy.
 * Live sync (rlantest / rlan.ctu.gov.cz) is next; keep RegulatorConnector for DE/AT/IT.
 */
export default function ConnectPanel() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setMsg(null);
    setOk(false);
    const em = email.trim();
    if (!em || !em.includes("@")) {
      setMsg("Zadejte platný e-mail k účtu ČTÚ RLAN.");
      return;
    }
    if (!password.trim()) {
      setMsg(
        "Zadejte heslo (uloží se jen lokálně až po zapnutí live sync — teď se nikam neposílá)."
      );
      return;
    }
    // Dry-run only — no network call to ČTÚ.
    setOk(true);
    setMsg(
      "Formulář je v pořádku. Live API sync (access-token na rlantest / rlan.ctu.gov.cz) ještě není zapnutý — demo zůstává upload-only."
    );
  }

  return (
    <div className="connect-shell">
      <div className="connect-status" role="status">
        <span className="dot" aria-hidden />
        <div>
          <strong>Stav připojení: připravujeme</strong>
          <span>
            Live sync ČTÚ RLAN API zatím vypnutý. MVP = upload CSV/XLSX, bez
            auto-prodloužení.
          </span>
        </div>
      </div>

      <form className="connect-form" onSubmit={onSubmit} noValidate>
        <div className="field">
          <label htmlFor="ctu-email">E-mail ČTÚ</label>
          <input
            id="ctu-email"
            type="email"
            autoComplete="username"
            placeholder="vas@firma.cz"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="ctu-password">Heslo</label>
          <input
            id="ctu-password"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <div className="notice" role="note" style={{ marginBottom: "1rem" }}>
          <strong>Brzy:</strong> přihlášení přes ČTÚ RLAN API (
          <code>rlantest.ctu.gov.cz</code> / <code>rlan.ctu.gov.cz</code>, access-token).
          Teď se údaje nikam neodesílají — jen kontrola formuláře.
        </div>

        <div className="cta-row">
          <button type="submit" className="btn btn-secondary">
            Ověřit formulář (dry-run)
          </button>
          <button
            type="button"
            className="btn"
            disabled
            title="Live sync přijde v další iteraci"
          >
            Připojit (brzy)
          </button>
        </div>

        {msg && (
          <div
            className={ok ? "ok-box" : "error"}
            role="status"
            style={{ marginTop: "1rem" }}
          >
            {msg}
          </div>
        )}
      </form>
    </div>
  );
}
