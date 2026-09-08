"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  AlertsPayload,
  BUCKET_LABELS,
  BUCKET_LABELS_CS,
  BUCKET_ORDER,
  BucketId,
  StationRow,
  stationsToCsv,
} from "../lib/domain";
import { loadSampleCsv, parseUploadedFile, rowsToAlerts } from "../lib/parseFile";
import { loadResult, saveResult, clearResult } from "../lib/storage";

function downloadBlob(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function UploadIcon() {
  return (
    <svg className="dropzone-icon" viewBox="0 0 48 48" fill="none" aria-hidden>
      <rect x="6" y="8" width="36" height="32" rx="8" stroke="currentColor" strokeWidth="2.5" />
      <path
        d="M24 30V16M24 16l-7 7M24 16l7 7"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function EmptyIllu() {
  return (
    <svg className="empty-illu" viewBox="0 0 64 64" fill="none" aria-hidden>
      <rect x="8" y="12" width="48" height="40" rx="10" fill="#CCFBF1" stroke="#0D9488" strokeWidth="2.5" />
      <path d="M20 28h24M20 36h16" stroke="#0D9488" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="48" cy="16" r="10" fill="#FEF3C7" stroke="#1C1917" strokeWidth="2" />
      <path d="M48 12v8M44 16h8" stroke="#1C1917" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function StationTable({ rows, empty }: { rows: StationRow[]; empty?: string }) {
  if (!rows.length) {
    return <p className="muted empty-hint">{empty ?? "Žádné stanice v tomto bucketu."}</p>;
  }
  return (
    <div className="table-scroll">
      <table className="data">
        <thead>
          <tr>
            <th>Volací znak</th>
            <th>Název</th>
            <th>Frekvence</th>
            <th>Konec platnosti</th>
            <th>Dní</th>
            <th>Ochrana do</th>
            <th>Horizont</th>
            <th>Akce</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((s) => (
            <tr
              key={`${s.callsign}-${s.valid_to}`}
              className={s.actionable ? "actionable" : undefined}
            >
              <td>
                <strong>{s.callsign}</strong>
              </td>
              <td>{s.name}</td>
              <td>{s.frequency_mhz}</td>
              <td>{s.valid_to_date ?? "—"}</td>
              <td>{s.days_to_valid_to ?? "—"}</td>
              <td>{s.protected_to_date ?? "—"}</td>
              <td>
                <span className={`bucket-tag ${s.valid_bucket}`}>
                  {BUCKET_LABELS_CS[s.valid_bucket]}
                </span>
              </td>
              <td>
                {s.actionable ? (
                  <span className="action-pill" title="Obnovit v portálu ČTÚ">
                    obnovit
                  </span>
                ) : (
                  ""
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Workspace() {
  const [payload, setPayload] = useState<AlertsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [busyLabel, setBusyLabel] = useState("Načítám…");
  const [dragOver, setDragOver] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const saved = loadResult();
    if (saved) setPayload(saved);
    setHydrated(true);
  }, []);

  useEffect(() => {
    return () => {
      if (toastTimer.current) clearTimeout(toastTimer.current);
    };
  }, []);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 6000);
  }, []);

  const applyRows = useCallback((rows: Record<string, unknown>[]) => {
    const result = rowsToAlerts(rows);
    setPayload(result);
    saveResult(result);
    setError(null);
  }, []);

  const onFiles = useCallback(
    async (files: FileList | File[] | null) => {
      if (!files || !files.length) return;
      const file = files[0];
      setBusy(true);
      setBusyLabel(`Zpracovávám ${file.name}…`);
      setError(null);
      try {
        const rows = await parseUploadedFile(file);
        applyRows(rows);
      } catch (e) {
        const msg = (e as Error).message || "Chyba při načítání souboru";
        setError(msg);
        showToast(msg);
      } finally {
        setBusy(false);
        if (inputRef.current) inputRef.current.value = "";
      }
    },
    [applyRows, showToast]
  );

  const onSample = useCallback(async () => {
    setBusy(true);
    setBusyLabel("Načítám ukázková data…");
    setError(null);
    try {
      const rows = await loadSampleCsv();
      applyRows(rows);
    } catch (e) {
      const msg = (e as Error).message || "Chyba při načítání ukázky";
      setError(msg);
      showToast(msg);
    } finally {
      setBusy(false);
    }
  }, [applyRows, showToast]);

  const byBucket = useMemo(() => {
    const map: Record<BucketId, StationRow[]> = {
      overdue: [],
      leq_30: [],
      leq_60: [],
      leq_90: [],
      later: [],
    };
    if (!payload) return map;
    for (const b of BUCKET_ORDER) {
      map[b] = (payload.buckets[BUCKET_LABELS[b]] as StationRow[]) ?? [];
    }
    return map;
  }, [payload]);

  const actionableCount = payload
    ? (payload.counts["overdue"] ?? 0) + (payload.counts["≤30"] ?? 0)
    : 0;

  return (
    <main className="container">
      {toast && (
        <div className="toast toast-error" role="alert">
          <strong>Chyba souboru</strong>
          <span>{toast}</span>
          <button
            type="button"
            className="toast-close"
            aria-label="Zavřít"
            onClick={() => setToast(null)}
          >
            ×
          </button>
        </div>
      )}

      <div className="page-head">
        <div>
          <h1>Pracovní plocha</h1>
          <p className="muted" style={{ marginTop: 0, marginBottom: 0 }}>
            Nahrajte export → bucket kalendář a alerty k obnově.{" "}
            <span className="badge badge-warn">bez auto-prodloužení</span>
          </p>
        </div>
        <Link href="/settings" className="btn btn-secondary btn-sm">
          Nastavení / ČTÚ
        </Link>
      </div>

      <div
        className={`dropzone ${dragOver ? "dragover" : ""} ${busy ? "busy" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (!busy) onFiles(e.dataTransfer.files);
        }}
        onClick={() => !busy && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-busy={busy}
        onKeyDown={(e) => {
          if (!busy && (e.key === "Enter" || e.key === " ")) inputRef.current?.click();
        }}
      >
        {busy ? (
          <>
            <div className="spinner" aria-hidden />
            <strong>{busyLabel}</strong>
            <p>Načítám datum konce platnosti…</p>
          </>
        ) : (
          <>
            <UploadIcon />
            <strong>Přetáhněte export stanic z ČTÚ</strong>
            <p>
              CSV nebo Excel. Potřebujeme sloupec s datem konce platnosti — obvykle z exportu portálu.
            </p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xlsm,.xls,text/csv"
          className="sr-only"
          disabled={busy}
          onChange={(e) => onFiles(e.target.files)}
        />
      </div>

      <div className="toolbar">
        <button type="button" className="btn" onClick={onSample} disabled={busy}>
          Načíst ukázková data
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => inputRef.current?.click()}
          disabled={busy}
        >
          Vybrat soubor
        </button>
        {payload && (
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              clearResult();
              setPayload(null);
              setError(null);
            }}
            disabled={busy}
          >
            Vymazat
          </button>
        )}
        {hydrated && payload && (
          <span className="muted">
            K {payload.as_of_date} (Europe/Prague) · {payload.stations.length} stanic
          </span>
        )}
      </div>

      {error && (
        <div className="error" role="alert">
          <strong>Nepodařilo se načíst soubor.</strong> {error}
        </div>
      )}

      {payload && (
        <>
          <div className="section-title" style={{ marginTop: "0.5rem" }}>
            <h2>Bucket kalendář</h2>
            <span className="muted">klikněte na kartu → skok na tabulku</span>
          </div>
          <div className="bucket-calendar-hint" aria-hidden>
            {BUCKET_ORDER.map((b) => (
              <span key={b} className={`bucket-tag ${b}`}>
                {BUCKET_LABELS_CS[b]}
              </span>
            ))}
          </div>

          <div className="summary summary-sticky" aria-label="Souhrn bucketů">
            {BUCKET_ORDER.map((b) => (
              <a key={b} href={`#bucket-${b}`} className={`summary-item ${b}`}>
                <span className="n">{payload.counts[BUCKET_LABELS[b]] ?? 0}</span>
                <span className="l">{BUCKET_LABELS_CS[b]}</span>
              </a>
            ))}
            <a href="#alerts" className="summary-item actionable">
              <span className="n">{actionableCount}</span>
              <span className="l">k obnově</span>
            </a>
          </div>

          <div className="toolbar">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() =>
                downloadBlob(
                  "spectrumdeadline-calendar.csv",
                  stationsToCsv(payload.stations),
                  "text/csv;charset=utf-8"
                )
              }
            >
              Export CSV
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() =>
                downloadBlob(
                  "spectrumdeadline-alerts.json",
                  JSON.stringify(payload, null, 2) + "\n",
                  "application/json"
                )
              }
            >
              Export JSON
            </button>
            <span className="badge badge-warn">bez auto-prodloužení</span>
          </div>

          <section id="alerts">
            <div className="section-title">
              <h2>K obnově (overdue ∪ ≤30)</h2>
              <span className="muted">{actionableCount} stanic · obnovte v portálu ČTÚ</span>
            </div>
            <div className={`card ${actionableCount ? "card-actionable" : ""}`}>
              <StationTable
                rows={payload.actionable}
                empty="Nic k obnově v horizontu 30 dní. Když nahráte soubor, „obnovit teď“ se objeví tady."
              />
            </div>
          </section>

          {BUCKET_ORDER.map((b) => (
            <section key={b} id={`bucket-${b}`}>
              <div className="section-title">
                <h2>
                  {BUCKET_LABELS_CS[b]}{" "}
                  <span className="muted">({BUCKET_LABELS[b]})</span>
                </h2>
                <span className="muted">{byBucket[b].length} stanic</span>
              </div>
              <div className="card">
                <StationTable rows={byBucket[b]} />
              </div>
            </section>
          ))}

          <p className="footer-note">
            SpectrumDeadline <strong>neobnovuje</strong> licence automaticky.
            Obnovu vždy děláte vy v portálu ČTÚ.
          </p>
        </>
      )}

      {!payload && hydrated && (
        <div className="card empty-state" style={{ marginTop: "1rem" }}>
          <EmptyIllu />
          <h3>Zatím žádné stanice</h3>
          <p className="muted">
            Nahrajte export — nebo vyzkoušejte ukázku.
          </p>
          <ol>
            <li>
              Nahrajte export stanic z ČTÚ (<strong>CSV / Excel</strong>), nebo klikněte „Načíst ukázková data“.
            </li>
            <li>
              Prohlédněte kalendář nahoře a sekci <strong>K obnově</strong> (do 30 dní).
            </li>
            <li>
              Exportujte CSV/JSON pro další práci — obnovu vždy děláte vy v portálu ČTÚ.
            </li>
          </ol>
          <div className="cta-row" style={{ marginBottom: "1rem" }}>
            <button type="button" className="btn" onClick={onSample} disabled={busy}>
              Načíst ukázková data
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => inputRef.current?.click()}
              disabled={busy}
            >
              Vybrat soubor
            </button>
          </div>
          <p className="muted" style={{ marginBottom: 0 }}>
            Přímé stažení ze ČTÚ přidáme později — zatím{" "}
            <Link href="/settings">Nastavení / ČTÚ</Link>.
          </p>
        </div>
      )}
    </main>
  );
}
