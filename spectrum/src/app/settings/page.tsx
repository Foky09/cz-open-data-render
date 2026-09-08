import Link from "next/link";
import ConnectPanel from "../../components/ConnectPanel";

export default function SettingsPage() {
  return (
    <main className="container">
      <div className="page-head">
        <div>
          <h1>Připojení ČTÚ (připravujeme)</h1>
          <p className="muted" style={{ marginTop: 0 }}>
            Teď funguje nahrání souboru. Přímé stažení ze ČTÚ přidáme později — obnovu vždy děláte vy v portálu ČTÚ.{" "}
            <span className="badge badge-warn">bez auto-prodloužení</span>
          </p>
        </div>
        <Link href="/app" className="btn btn-secondary btn-sm">
          Zpět na pracovní plochu
        </Link>
      </div>

      <section className="card">
        <h2>ČTÚ účet</h2>
        <p className="muted">
          Až bude sync hotový, stáhneme stanice přímo ze ČTÚ místo uploadu.
        </p>
        <ConnectPanel />
      </section>

      <section className="card">
        <h2>Co funguje teď</h2>
        <ul className="muted" style={{ marginBottom: 0 }}>
          <li>Upload CSV / Excel → kalendář + stanice k obnově</li>
          <li>
            <strong>Bez auto-prodloužení</strong> — obnovu děláte vy v portálu ČTÚ
          </li>
        </ul>
      </section>

      <section className="card">
        <h2>Roadmapa</h2>
        <div className="grid-2">
          <div>
            <span className="badge">teď</span>
            <p className="muted" style={{ margin: "0.5rem 0 0" }}>
              Nahrání souboru a kalendář obnov.
            </p>
          </div>
          <div>
            <span className="badge badge-warn">brzy</span>
            <p className="muted" style={{ margin: "0.5rem 0 0" }}>
              Přímé stažení ze ČTÚ — pořád bez auto-prodloužení.
            </p>
          </div>
        </div>
      </section>

      <p className="footer-note">
        SpectrumDeadline · bez auto-prodloužení
      </p>
    </main>
  );
}
