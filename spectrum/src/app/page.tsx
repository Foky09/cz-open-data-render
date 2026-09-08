import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="container">
      <section className="hero">
        <span className="badge badge-warn">bez auto-prodloužení / no auto-renew</span>
        <h1>Kalendář obnov ČTÚ RLAN pro WISP</h1>
        <p className="lead">
          Nahrajte export stanic (CSV/XLSX) a hned uvidíte, které licence končí —
          po termínu, ≤30, ≤60, ≤90 dní. SpectrumDeadline jen upozorňuje;{" "}
          <strong>neobnovuje automaticky</strong> (bez auto-prodloužení).
        </p>
        <p className="muted" style={{ marginTop: "-0.75rem", marginBottom: "1.25rem" }}>
          EN: Upload station export → renewal calendar + actionable alerts. No auto-renew.
        </p>
        <div className="cta-row">
          <Link href="/app" className="btn">
            Otevřít pracovní plochu
          </Link>
          <Link href="/app" className="btn btn-secondary">
            Načíst ukázková data
          </Link>
          <Link href="/settings" className="btn btn-ghost">
            Nastavení ČTÚ (brzy)
          </Link>
        </div>
      </section>

      <div className="notice" role="note">
        <strong>Hranice produktu:</strong> žádné automatické prodloužení licence (bez
        auto-prodloužení). Obnovu provádíte vy v portálu ČTÚ (typicky když zbývá &lt;1
        měsíc). Tento nástroj = kalendář + alerty ze souboru stanic.
      </div>

      <section style={{ marginTop: "2rem" }}>
        <div className="grid-3">
          <div className="card feature">
            <h3>1. Upload</h3>
            <p>
              CSV nebo XLSX s <code>valid_to</code> (unix / ISO, i smíšeně). Volitelně{" "}
              <code>protected_to</code>, callsign, name, frekvence.
            </p>
          </div>
          <div className="card feature">
            <h3>2. Bucket kalendář</h3>
            <p>
              Cyklus 12 + 6 = 18 měsíců. Bucket podle dní do <code>valid_to</code>{" "}
              (Europe/Prague): po termínu / ≤30 / ≤60 / ≤90 / později.
            </p>
          </div>
          <div className="card feature">
            <h3>3. Alerty k obnově</h3>
            <p>
              K obnově = overdue ∪ ≤30. Export CSV/JSON. Bez auto-prodloužení — výsledek
              zůstane v prohlížeči (localStorage).
            </p>
          </div>
        </div>
      </section>

      <section className="card" style={{ marginTop: "1.5rem" }}>
        <h2>Doménová pravidla</h2>
        <ul className="muted">
          <li>
            Oficiální cyklus:{" "}
            <strong>12 měsíců platnost + 6 měsíců ochrana = 18 měsíců</strong>
          </li>
          <li>Portál umožňuje obnovu typicky při &lt;1 měsíci → actionable ≤30 dní</li>
          <li>
            Časová zóna výpočtu: <strong>Europe/Prague</strong>
          </li>
          <li>MVP: upload-only (live ČTÚ API sync připravujeme — viz Nastavení)</li>
        </ul>
      </section>

      <p className="footer-note">
        SpectrumDeadline MVP · Česky-first UI · bez auto-prodloužení / no auto-renew
      </p>
    </main>
  );
}
