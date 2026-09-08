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

function IconCalm() {
  return (
    <svg className="feat-icon" viewBox="0 0 40 40" fill="none" aria-hidden>
      <rect width="40" height="40" rx="12" fill="#CCFBF1" />
      <path d="M12 22c2-4 5-6 8-6s6 2 8 6" stroke="#0D9488" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="16" cy="18" r="1.5" fill="#0D9488" />
      <circle cx="24" cy="18" r="1.5" fill="#0D9488" />
      <path d="M14 27h12" stroke="#0D9488" strokeWidth="2.5" strokeLinecap="round" />
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
            <span className="badge badge-warn">Pro české WISP · kalendář obnov RLAN</span>
            <h1>Které stanice obnovit v příštích 90 dnech — ať nespadne pokrytí</h1>
            <p className="lead">
              Nahrajete export stanic z ČTÚ a hned vidíte: po termínu, do 30 / 60 / 90 dní.
              Jen připomínáme — obnovu děláte vy v portálu ČTÚ.
            </p>
            <div className="cta-row">
              <Link href="/app" className="btn">
                Ukázat stanice k obnově
              </Link>
              <Link href="/app" className="btn btn-secondary">
                Vyzkoušet na ukázce
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
        provádíte vy v portálu ČTÚ. Tento nástroj = kalendář + připomínky ze souboru stanic.
      </div>

      <section className="landing-section" aria-labelledby="benefits-heading">
        <h2 id="benefits-heading">Proč SpectrumDeadline</h2>
        <div className="grid-3">
          <div className="card feature">
            <span className="feature-num" aria-hidden>
              01
            </span>
            <IconCalm />
            <h3>Klid místo půlnocního Excelu</h3>
            <p>Přehled naléhavosti bez ručního sledování desítek termínů.</p>
          </div>
          <div className="card feature">
            <span className="feature-num" aria-hidden>
              02
            </span>
            <IconBuckets />
            <h3>Jasná fronta „obnovit teď“</h3>
            <p>Po termínu + do 30 dní — víte, co řešit jako první.</p>
          </div>
          <div className="card feature">
            <span className="feature-num" aria-hidden>
              03
            </span>
            <IconAlert />
            <h3>Bez automatického prodloužení</h3>
            <p>Rozhodujete vy. My jen připomínáme a exportujeme seznam.</p>
          </div>
        </div>
      </section>

      <section className="landing-section" aria-labelledby="how-heading">
        <h2 id="how-heading">Jak to funguje</h2>
        <div className="steps">
          <div className="step-card">
            <h3>1. Stáhnete seznam</h3>
            <p>Stáhnete seznam stanic z portálu ČTÚ.</p>
          </div>
          <div className="step-card">
            <h3>2. Přetáhnete soubor</h3>
            <p>Soubor sem přetáhnete (nebo vyzkoušíte ukázku).</p>
          </div>
          <div className="step-card">
            <h3>3. Kalendář + export</h3>
            <p>Vidíte kalendář podle naléhavosti a export „k obnově“.</p>
          </div>
        </div>
      </section>

      <section className="cta-banner" aria-labelledby="cta-heading">
        <h2 id="cta-heading">Připraveni na další obnovovací vlnu?</h2>
        <p>
          Otevřete pracovní plochu, nahrajte export — nebo nejdřív vyzkoušejte ukázková
          data.
        </p>
        <div className="cta-row">
          <Link href="/app" className="btn">
            Ukázat stanice k obnově
          </Link>
          <Link href="/app" className="btn btn-secondary">
            Vyzkoušet na ukázce
          </Link>
        </div>
      </section>

      <p className="footer-note">
        Obnovu provádíte v ČTÚ · žádné auto-prodloužení.
      </p>
    </main>
  );
}
