import type { Metadata } from "next";
import Link from "next/link";
import { Fraunces, Nunito_Sans } from "next/font/google";
import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin", "latin-ext"],
  variable: "--font-fraunces",
  display: "swap",
  adjustFontFallback: false,
});

const nunito = Nunito_Sans({
  subsets: ["latin", "latin-ext"],
  variable: "--font-nunito",
  display: "swap",
  adjustFontFallback: false,
});

export const metadata: Metadata = {
  title: "SpectrumDeadline — kalendář obnov RLAN pro WISP",
  description:
    "Nahrajte export stanic ČTÚ a hned uvidíte, co končí. Bucket kalendář + alerty k obnově. Bez auto-prodloužení.",
};

function BrandMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 32 32" aria-hidden>
      <rect width="32" height="32" rx="8" fill="#0D9488" />
      <rect x="7" y="18" width="4" height="7" rx="1.5" fill="#F7F4EF" />
      <rect x="14" y="12" width="4" height="13" rx="1.5" fill="#FEF3C7" />
      <rect x="21" y="8" width="4" height="17" rx="1.5" fill="#F7F4EF" />
    </svg>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="cs" className={`${fraunces.variable} ${nunito.variable}`}>
      <body>
        <header className="site-header">
          <Link href="/" className="brand">
            <BrandMark />
            Spectrum<span>Deadline</span>
          </Link>
          <nav className="nav">
            <Link href="/">Úvod</Link>
            <Link href="/app">Pracovní plocha</Link>
            <Link href="/app#alerts">K obnově</Link>
            <Link href="/settings">Nastavení</Link>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
