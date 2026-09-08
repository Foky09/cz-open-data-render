import Link from "next/link";
import ConnectPanel from "@/components/ConnectPanel";

export default function SettingsPage() {
  return (
    <main className="container">
      <div className="page-head">
        <div>
          <h1 style={{ marginBottom: "0.35rem" }}>Nastavení / Připojení ČTÚ</h1>
          <p className="muted" style={{ marginTop: 0 }}>
            Stub pro budoucí live sync.{" "}
            <span className="badge badge-warn">bez auto-prodloužení</span>
          </p>
        </div>
        <Link href="/app" className="btn btn-secondary btn-sm">
          Zpět na pracovní plochu
        </Link>
      </div>

      <section className="card">
        <h2>ČTÚ RLAN účet</h2>
        <p className="muted">
          Až bude sync hotový, stáhneme stanice přímo z API místo uploadu. Abstrakce{" "}
          <code>RegulatorConnector</code> zůstává — další země (DE / AT / IT) se připojí
          stejně.
        </p>
        <ConnectPanel />
      </section>

      <section className="card">
        <h2>Co funguje teď</h2>
        <ul className="muted">
          <li>Upload CSV / XLSX → bucket kalendář + alerty k obnově</li>
          <li>Datumy: unix i ISO (i smíšeně v jednom souboru)</li>
          <li>
            <strong>Bez auto-prodloužení</strong> — obnovu děláte vy v portálu ČTÚ
          </li>
        </ul>
      </section>

      <p className="footer-note">
        SpectrumDeadline MVP · CZ-first · EN secondary · No auto-renew
      </p>
    </main>
  );
}
