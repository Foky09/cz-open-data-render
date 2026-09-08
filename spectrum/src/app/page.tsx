import Link from "next/link";

function HeroVisual() {
  return (
    <svg
      className="hero-blob"
      viewBox="0 0 320 280"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <path
        d="M40 160c0-70 50-120 120-120s120 40 120 100-45 110-120 110S40 230 40 160z"
        fill="#CCFBF1"
      />
      <path
        d="M70 170c10-55 55-90 105-90s95 30 95 80-35 95-100 95-110-30-100-85z"
        fill="#F7F4EF"
        stroke="#0D9488"
        strokeWidth="3"
      />
      {/* calendar card */}
      <rect x="95" y="70" width="130" height="150" rx="14" fill="#FFFCFA" stroke="#1C1917" strokeWidth="2.5" />
      <rect x="95" y="70" width="130" height="36" rx="14" fill="#0D9488" />
      <rect x="95" y="92" width="130" height="14" fill="#0D9488" />
      <text x="160" y="94" textAnchor="middle" fill="#F7F4EF" fontSize="13" fontWeight="700" fontFamily="system-ui">
        Obnovy RLAN
      </text>
      {/* bucket dots */}
      <circle cx="120" cy="130" r="10" fill="#FEE2E2" stroke="#DC2626" strokeWidth="2" />
      <circle cx="160" cy="130" r="10" fill="#FFEDD5" stroke="#EA580C" strokeWidth="2" />
      <circle cx="200" cy="130" r="10" fill="#FEF3C7" stroke="#CA8A04" strokeWidth="2" />
      <circle cx="120" cy="170" r="10" fill="#CCFBF1" stroke="#0D9488" strokeWidth="2" />
      <circle cx="160" cy="170" r="10" fill="#F5F5F4" stroke="#78716C" strokeWidth="2" />
      <rect x="110" y="195" width="100" height="10" rx="5" fill="#E7E0D5" />
      <rect x="110" y="212" width="70" height="10" rx="5" fill="#CCFBF1" />
      {/* playful antenna */}
      <path d="M250 55 L250 30 M235 45 L265 45" stroke="#1C1917" strokeWidth="3" strokeLinecap="round" />
      <circle cx="250" cy="55" r="8" fill="#FEF3C7" stroke="#1C1917" strokeWidth="2.5" />
      <path d="M250 63 v40" stroke="#1C1917" strokeWidth="2.5" />
      <path d="M235 110 Q250 95 265 110" stroke="#0D9488" strokeWidth="2.5" fill="none" />
      <path d="M225 122 Q250 100 275 122" stroke="#0D9488" strokeWidth="2" fill="none" opacity="0.5" />
    </svg>
  );
}

function IconUpload() {
  return (
    <svg className="feat-icon" viewBox="0 0 40 40" fill="none" aria-hidden>
      <rect width="40" height="40" rx="12" fill="#CCFBF1" />
      <path d="M20 28V14M20 14l-6 6M20 14l6 6" stroke="#0D9488" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 30h16" stroke="#0D9488" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

function IconBuckets() {
  return (
    <svg className="feat-icon" viewBox="0 0 40 40" fill="none" aria-hidden>
      <rect width="40" height="40" rx="12" fill="#FEF3C7" />
      <rect x="8" y="12" width="8" height="18" rx="2" fill="#DC2626" opacity="0.85" />
      <rect x="16" y="16" width="8" height="14" rx="2" fill="#EA580C" opacity="0.85" />
      <rect x="24" y="20" width="8" height="10" rx="2" fill="#0D9488" opacity="0.85" />
    </svg>
  );
}

function IconAlert() {
  return (
    <svg className="feat-icon" viewBox="0 0 40 40" fill="none" aria-hidden>
      <rect width="40" height="40" rx="12" fill="#FFEDD5" />
      <path d="M20 11l11 19H9L20 11z" stroke="#EA580C" strokeWidth="2.5" strokeLinejoin="round" fill="#FEF3C7" />
      <path d="M20 18v6" stroke="#9A3412" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="20" cy="27" r="1.4" fill="#9A3412" />
    </svg>
  );
}

export default function LandingPage() {
  return (
    <main className="container">
      <section className="hero">
        <div className="hero-grid">
          <div>
            <span className="badge badge-warn">bez auto-prodloužení</span>
            <h1>Licence RLAN pod kontrolou — ne v Excelu o půlnoci</h1>
            <p className="lead">
              SpectrumDeadline je kalendář obnov pro české WISP: nahrajete export stanic
              z ČTÚ a hned vidíte, co je po termínu, co hoří do 30 dní a co ještě počká.
              Jen upozorňujeme — <strong>neobnovujeme automaticky</strong>.
            </p>
            <div className="cta-row">
              <Link href="/app" className="btn">
                Otevřít pracovní plochu
              </Link>
              <Link href="/app" className="btn btn-secondary">
                Vyzkoušet na ukázce
              </Link>
              <Link href="/settings" className="btn btn-ghost">
                Nastavení ČTÚ →
              </Link>
            </div>
          </div>
          <div className="hero-visual">
            <HeroVisual />
          </div>
        </div>
      </section>

      <div className="notice" role="note">
        <strong>Hranice produktu:</strong> žádné automatické prodloužení licence. Obnovu
        provádíte vy v portálu ČTÚ (typicky když zbývá &lt;1 měsíc). Tento nástroj =
        kalendář + alerty ze souboru stanic.
      </div>

      <section className="landing-section" aria-labelledby="problem-heading">
        <h2 id="problem-heading">Proč WISP ztrácejí klid</h2>
        <p className="section-lead">
          RLAN cyklus je 12 + 6 měsíců. Portál pustí obnovu až těsně před koncem. Bez
          přehledu se to snadno přehlédne.
        </p>
        <ul className="problem-list">
          <li>
            <span className="emoji" aria-hidden>
              📡
            </span>
            <div>
              <strong>Desítky (nebo stovky) stanic</strong>
              <span>
                Každá má jiné valid_to. Sledovat to v tabulce ručně je náchylné na chyby.
              </span>
            </div>
          </li>
          <li>
            <span className="emoji" aria-hidden>
              ⏰
            </span>
            <div>
              <strong>Okno obnovy je krátké</strong>
              <span>
                Typicky &lt;1 měsíc před koncem platnosti — kdo nemá alert, riskuje výpadek
                pokrytí.
              </span>
            </div>
          </li>
          <li>
            <span className="emoji" aria-hidden>
              🧾
            </span>
            <div>
              <strong>Export z ČTÚ ≠ srozumitelný plán</strong>
              <span>
                Unix timestampy a smíšená data. Potřebujete bucket kalendář, ne další
                sloupec.
              </span>
            </div>
          </li>
        </ul>
      </section>

      <section className="landing-section" aria-labelledby="how-heading">
        <h2 id="how-heading">Jak to funguje</h2>
        <p className="section-lead">
          Tři kroky. Žádný účet, data zůstanou v prohlížeči (localStorage).
        </p>
        <div className="steps">
          <div className="step-card">
            <h3>Upload</h3>
            <p>
              Přetáhněte CSV nebo XLSX export stanic. Povinný sloupec{" "}
              <code>valid_to</code> (unix i ISO, i smíšeně).
            </p>
          </div>
          <div className="step-card">
            <h3>Bucket kalendář</h3>
            <p>
              Spočítáme dny do konce (Europe/Prague) a roztřídíme: po termínu / ≤30 / ≤60
              / ≤90 / později.
            </p>
          </div>
          <div className="step-card">
            <h3>Obnova u ČTÚ</h3>
            <p>
              Sekce <strong>K obnově</strong> = overdue ∪ ≤30. Export CSV/JSON — obnovu
              provedete vy v portálu.
            </p>
          </div>
        </div>
      </section>

      <section className="landing-section" aria-labelledby="features-heading">
        <h2 id="features-heading">Co dostanete</h2>
        <p className="section-lead">
          Nástroj pro operátory, ne další generický dashboard.
        </p>
        <div className="grid-3">
          <div className="card feature">
            <span className="feature-num" aria-hidden>
              01
            </span>
            <IconUpload />
            <h3>Chytrý parser</h3>
            <p>
              Unix, ISO, Excel serial, české <code>DD.MM.YYYY</code> — i v jednom souboru.
              Volitelně callsign, name, frekvence, protected_to.
            </p>
          </div>
          <div className="card feature">
            <span className="feature-num" aria-hidden>
              02
            </span>
            <IconBuckets />
            <h3>Bucket přehled</h3>
            <p>
              Sticky souhrn + tabulky podle urgency. Cyklus 12 + 6 = 18 měsíců je v
              doménových pravidlech.
            </p>
          </div>
          <div className="card feature">
            <span className="feature-num" aria-hidden>
              03
            </span>
            <IconAlert />
            <h3>Actionable alerty</h3>
            <p>
              Jasný seznam „obnovit teď“. Bez auto-prodloužení — výsledek můžete exportovat
              do svého workflow.
            </p>
          </div>
        </div>
      </section>

      <section className="card landing-section" style={{ marginTop: "2rem" }}>
        <h2 style={{ marginTop: 0 }}>Doménová pravidla</h2>
        <ul className="muted" style={{ marginBottom: 0 }}>
          <li>
            Oficiální cyklus:{" "}
            <strong>12 měsíců platnost + 6 měsíců ochrana = 18 měsíců</strong>
          </li>
          <li>Portál umožňuje obnovu typicky při &lt;1 měsíci → actionable ≤30 dní</li>
          <li>
            Časová zóna výpočtu: <strong>Europe/Prague</strong>
          </li>
          <li>
            MVP: upload-only (live ČTÚ API sync připravujeme — viz{" "}
            <Link href="/settings">Nastavení</Link>)
          </li>
        </ul>
      </section>

      <section className="cta-banner" aria-labelledby="cta-heading">
        <h2 id="cta-heading">Připraveni na další obnovovací vlnu?</h2>
        <p>
          Otevřete pracovní plochu, nahrajte export — nebo nejdřív vyzkoušejte ukázková
          data.
        </p>
        <div className="cta-row">
          <Link href="/app" className="btn">
            Jít do aplikace
          </Link>
          <Link href="/settings" className="btn btn-secondary">
            Připojení ČTÚ (brzy)
          </Link>
        </div>
      </section>

      <p className="footer-note">
        SpectrumDeadline MVP · Česky-first UI · bez auto-prodloužení / no auto-renew
      </p>
    </main>
  );
}
