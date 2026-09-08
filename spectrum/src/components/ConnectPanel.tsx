"use client";

export default function ConnectPanel() {
  return (
    <div className="connect-shell">
      <div className="connect-status" role="status">
        <span className="dot" aria-hidden />
        <div>
          <strong>Připojení ČTÚ (připravujeme)</strong>
          <span>
            Teď funguje nahrání souboru. Přímé stažení ze ČTÚ přidáme později — obnovu vždy děláte vy v portálu ČTÚ.
          </span>
        </div>
      </div>

      <form className="connect-form" onSubmit={(e) => e.preventDefault()} noValidate>
        <div className="field">
          <label htmlFor="ctu-email">E-mail ČTÚ <span className="badge">Brzy</span></label>
          <input
            id="ctu-email"
            type="email"
            autoComplete="username"
            placeholder="vas@firma.cz"
            disabled
          />
        </div>
        <div className="field">
          <label htmlFor="ctu-password">Heslo <span className="badge">Brzy</span></label>
          <input
            id="ctu-password"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            disabled
          />
        </div>

        <div className="notice" role="note" style={{ marginBottom: "1rem" }}>
          <strong>Brzy:</strong> přímé stažení stanic ze ČTÚ. Teď stačí nahrát export na pracovní ploše.
        </div>

        <div className="cta-row">
          <button
            type="button"
            className="btn"
            disabled
            title="Přímé stažení ze ČTÚ přijde později"
          >
            Připojit (Brzy)
          </button>
        </div>
      </form>
    </div>
  );
}
