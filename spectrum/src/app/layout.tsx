import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "SpectrumDeadline — kalendář obnov RLAN",
  description:
    "Kalendář a alerty pro obnovu ČTÚ RLAN stanic. Bez auto-prodloužení. Upload CSV/XLSX → bucket calendar.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="cs">
      <body>
        <header className="site-header">
          <Link href="/" className="brand">
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
