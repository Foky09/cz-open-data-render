/**
 * SpectrumDeadline calendar/alerts core.
 * Operates on NormalizedStation from RegulatorConnector — no ČTÚ column names here.
 * Cycle: 12mo valid + 6mo protected = 18mo. No auto-renew.
 * Buckets by days until valid_to (Europe/Prague).
 */

import type { NormalizedStation } from "./connectors/types";

export type BucketId = "overdue" | "leq_30" | "leq_60" | "leq_90" | "later";

export const BUCKET_ORDER: BucketId[] = [
  "overdue",
  "leq_30",
  "leq_60",
  "leq_90",
  "later",
];

export const BUCKET_LABELS: Record<BucketId, string> = {
  overdue: "overdue",
  leq_30: "≤30",
  leq_60: "≤60",
  leq_90: "≤90",
  later: "later",
};

export const BUCKET_LABELS_CS: Record<BucketId, string> = {
  overdue: "po termínu",
  leq_30: "≤30 dní",
  leq_60: "≤60 dní",
  leq_90: "≤90 dní",
  later: "později",
};

/** Enriched calendar row (regulator-agnostic display fields). */
export interface StationRow {
  /** Same as NormalizedStation.id; also exported as callsign for CSV compat */
  callsign: string;
  name: string;
  frequency_mhz: string;
  valid_to: number | null;
  protected_to: number | null;
  registered_at: number | null;
  updated_at: number | null;
  valid_to_date: string | null;
  protected_to_date: string | null;
  days_to_valid_to: number | null;
  days_to_protected_to: number | null;
  valid_bucket: BucketId;
  protected_bucket: BucketId;
  actionable: boolean;
  regulator: string;
}

export interface AlertsPayload {
  generated_at: string;
  as_of_date: string;
  timezone: string;
  regulator: string;
  policy: {
    valid_months: number;
    protected_months: number;
    total_cycle_months: number;
    actionable_days: number;
    note: string;
  };
  counts: Record<string, number>;
  buckets: Record<string, StationRow[]>;
  actionable: StationRow[];
  stations: StationRow[];
}

const TZ = "Europe/Prague";

export function todayPrague(now: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now);
}

function datePartsInTz(tsSec: number): { y: number; m: number; d: number } {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date(tsSec * 1000));
  const get = (t: string) =>
    Number(parts.find((p) => p.type === t)?.value ?? "0");
  return { y: get("year"), m: get("month"), d: get("day") };
}

function parseYmd(ymd: string): { y: number; m: number; d: number } {
  const [y, m, d] = ymd.split("-").map(Number);
  return { y, m, d };
}

export function daysUntil(targetYmd: string | null, todayYmd: string): number | null {
  if (!targetYmd) return null;
  const a = parseYmd(todayYmd);
  const b = parseYmd(targetYmd);
  const utcA = Date.UTC(a.y, a.m - 1, a.d);
  const utcB = Date.UTC(b.y, b.m - 1, b.d);
  return Math.round((utcB - utcA) / 86_400_000);
}

export function unixToDateYmd(ts: number | null): string | null {
  if (ts === null || ts === undefined) return null;
  const { y, m, d } = datePartsInTz(ts);
  return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

/** Convert Y-M-D calendar date in Europe/Prague to unix seconds (local midnight). */
function pragueYmdToUnix(y: number, m: number, d: number): number {
  let guess = Date.UTC(y, m - 1, d, 0, 0, 0) / 1000;
  for (let i = 0; i < 48; i++) {
    const parts = datePartsInTz(guess);
    if (parts.y === y && parts.m === m && parts.d === d) {
      const hourParts = new Intl.DateTimeFormat("en-GB", {
        timeZone: TZ,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      }).formatToParts(new Date(guess * 1000));
      const get = (t: string) =>
        Number(hourParts.find((p) => p.type === t)?.value ?? "0");
      return guess - get("hour") * 3600 - get("minute") * 60 - get("second");
    }
    const want = Date.UTC(y, m - 1, d);
    const have = Date.UTC(parts.y, parts.m - 1, parts.d);
    const dayDiff = Math.round((want - have) / 86_400_000);
    guess += dayDiff * 86400;
    if (dayDiff === 0) break;
  }
  return Math.floor(guess);
}

/** Parse unix seconds (int/float/str) or ISO / common date strings. Shared by connectors. */
export function parseUnixish(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "boolean") return null;

  if (typeof value === "number") {
    if (Number.isNaN(value)) return null;
    const v = value;
    if (v > 1e9) {
      if (v > 1e12) return Math.floor(v / 1000);
      return Math.floor(v);
    }
    if (v > 20000 && v < 100000) {
      const excelEpoch = Date.UTC(1899, 11, 30);
      const ms = excelEpoch + v * 86_400_000;
      const dt = new Date(ms);
      return pragueYmdToUnix(dt.getUTCFullYear(), dt.getUTCMonth() + 1, dt.getUTCDate());
    }
    return Math.floor(v);
  }

  const s = String(value).trim();
  if (!s || ["nan", "none", "null"].includes(s.toLowerCase())) return null;

  if (/^-?\d+(\.\d+)?$/.test(s)) {
    return parseUnixish(Number(s));
  }

  const formats: Array<{ re: RegExp; order: "ymd" | "dmy" }> = [
    { re: /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}):(\d{2}))?/, order: "ymd" },
    { re: /^(\d{2})\.(\d{2})\.(\d{4})$/, order: "dmy" },
    { re: /^(\d{2})\/(\d{2})\/(\d{4})$/, order: "dmy" },
  ];

  for (const fmt of formats) {
    const m = s.match(fmt.re);
    if (!m) continue;
    let y: number, mo: number, d: number;
    if (fmt.order === "ymd") {
      y = Number(m[1]);
      mo = Number(m[2]);
      d = Number(m[3]);
    } else {
      d = Number(m[1]);
      mo = Number(m[2]);
      y = Number(m[3]);
    }
    return pragueYmdToUnix(y, mo, d);
  }

  throw new Error(`Nelze zpracovat datum/unix: ${JSON.stringify(value)} (očekáván unix nebo ISO YYYY-MM-DD)`);
}

export function bucketFor(days: number | null): BucketId {
  if (days === null || days === undefined) return "later";
  if (days < 0) return "overdue";
  if (days <= 30) return "leq_30";
  if (days <= 60) return "leq_60";
  if (days <= 90) return "leq_90";
  return "later";
}


function foldKey(s: string): string {
  return s.normalize("NFD").replace(/\p{M}/gu, "");
}
/** Map ČTÚ-like / Czech export headers onto canonical keys. */
export function normalizeHeader(h: string): string {
  const raw = h
    .trim()
    .toLowerCase()
    .normalize("NFKC")
    .replace(/^\uFEFF/, "")
    .replace(/[\s\-]+/g, "_")
    .replace(/_+/g, "_");
  const aliases: Record<string, string> = {
    konec_platnosti: "valid_to",
    platnost_do: "valid_to",
    platnost_konec: "valid_to",
    platny_do: "valid_to",
    platný_do: "valid_to",
    validto: "valid_to",
    valid_until: "valid_to",
    expiry: "valid_to",
    expires: "valid_to",
    expiry_date: "valid_to",
    date_to: "valid_to",
    do: "valid_to",
    konec: "valid_to",
    ochrana_do: "protected_to",
    protectedto: "protected_to",
    protected_until: "protected_to",
    volaci_znak: "callsign",
    volací_znak: "callsign",
    znacka: "callsign",
    značka: "callsign",
    station_id: "callsign",
    station_callsign: "callsign",
    id_stanice: "callsign",
    nazev: "name",
    název: "name",
    station_name: "name",
    nazev_stanice: "name",
    frekvence: "frequency_mhz",
    frequency: "frequency_mhz",
    freq: "frequency_mhz",
    mhz: "frequency_mhz",
    registrovano: "registered_at",
    registrováno: "registered_at",
    registered: "registered_at",
    aktualizovano: "updated_at",
    aktualizováno: "updated_at",
    updated: "updated_at",
  };
  return aliases[raw] ?? aliases[foldKey(raw)] ?? raw;
}

/** Enrich normalized stations into calendar rows (buckets, days, actionable). */
export function enrichNormalized(
  stations: NormalizedStation[],
  todayYmd: string
): StationRow[] {
  return stations.map((n) => {
    const v_date = unixToDateYmd(n.valid_to);
    const p_date = unixToDateYmd(n.protected_to);
    const d_valid = daysUntil(v_date, todayYmd);
    const d_prot = daysUntil(p_date, todayYmd);
    return {
      callsign: n.id,
      name: n.name,
      frequency_mhz: n.frequency,
      valid_to: n.valid_to,
      protected_to: n.protected_to,
      registered_at: n.registered_at,
      updated_at: n.updated_at,
      valid_to_date: v_date,
      protected_to_date: p_date,
      days_to_valid_to: d_valid,
      days_to_protected_to: d_prot,
      valid_bucket: bucketFor(d_valid),
      protected_bucket: bucketFor(d_prot),
      actionable: d_valid !== null && d_valid <= 30,
      regulator: n.regulator,
    };
  });
}

export function sortStations(stations: StationRow[]): StationRow[] {
  return [...stations].sort((a, b) => {
    const bi =
      BUCKET_ORDER.indexOf(a.valid_bucket) - BUCKET_ORDER.indexOf(b.valid_bucket);
    if (bi !== 0) return bi;
    const da = a.days_to_valid_to ?? 1e9;
    const db = b.days_to_valid_to ?? 1e9;
    if (da !== db) return da - db;
    return a.callsign.localeCompare(b.callsign);
  });
}

export function buildAlertsPayload(
  stations: StationRow[],
  todayYmd: string,
  regulator = "CZ-CTU",
  now: Date = new Date()
): AlertsPayload {
  const byBucket: Record<BucketId, StationRow[]> = {
    overdue: [],
    leq_30: [],
    leq_60: [],
    leq_90: [],
    later: [],
  };
  for (const s of stations) {
    byBucket[s.valid_bucket].push(s);
  }
  const counts: Record<string, number> = {};
  for (const b of BUCKET_ORDER) {
    counts[BUCKET_LABELS[b]] = byBucket[b].length;
  }
  return {
    generated_at: now.toISOString(),
    as_of_date: todayYmd,
    timezone: TZ,
    regulator,
    policy: {
      valid_months: 12,
      protected_months: 6,
      total_cycle_months: 18,
      actionable_days: 30,
      note: "Bez auto-prodloužení. Obnova v portálu ČTÚ typicky při <1 měsíci; tento nástroj jen kalendář + alerty.",
    },
    counts,
    buckets: Object.fromEntries(
      BUCKET_ORDER.map((b) => [BUCKET_LABELS[b], byBucket[b]])
    ),
    actionable: [...byBucket.overdue, ...byBucket.leq_30],
    stations,
  };
}

export function parseCsvText(text: string): Record<string, unknown>[] {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/).filter((l) => l.trim() !== "");
  if (lines.length === 0) throw new Error("CSV je prázdný. Nahrajte export stanic z ČTÚ (CSV/XLSX).");
  const delim = detectCsvDelimiter(lines[0]);
  const headers = parseCsvLine(lines[0], delim).map(normalizeHeader);
  if (!headers.length) throw new Error("CSV nemá hlavičku. Očekáván export stanic z ČTÚ.");
  if (!headers.includes("valid_to")) {
    throw new Error(
      "V souboru chybí datum konce platnosti. V exportu ČTÚ hledejte sloupec s koncem platnosti (např. valid_to, Konec platnosti, Platnost do)."
    );
  }
  const rows: Record<string, unknown>[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = parseCsvLine(lines[i], delim);
    if (cols.every((c) => c.trim() === "")) continue;
    const row: Record<string, unknown> = {};
    headers.forEach((h, j) => {
      row[h] = cols[j] ?? "";
    });
    rows.push(row);
  }
  if (!rows.length) {
    throw new Error("CSV má jen hlavičku — chybí datové řádky stanic.");
  }
  return rows;
}

function detectCsvDelimiter(headerLine: string): "," | ";" {
  const commas = parseCsvLine(headerLine, ",").length;
  const semis = parseCsvLine(headerLine, ";").length;
  return semis > commas ? ";" : ",";
}

function parseCsvLine(line: string, delim: "," | ";" = ","): string[] {
  const out: string[] = [];
  let cur = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inQuotes) {
      if (ch === '"') {
        if (line[i + 1] === '"') {
          cur += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        cur += ch;
      }
    } else {
      if (ch === '"') inQuotes = true;
      else if (ch === delim) {
        out.push(cur);
        cur = "";
      } else cur += ch;
    }
  }
  out.push(cur);
  return out;
}

export function stationsToCsv(stations: StationRow[]): string {
  const fields = [
    "callsign",
    "name",
    "frequency_mhz",
    "valid_to",
    "valid_to_date",
    "days_to_valid_to",
    "valid_bucket",
    "protected_to",
    "protected_to_date",
    "days_to_protected_to",
    "protected_bucket",
    "actionable",
    "registered_at",
    "updated_at",
    "regulator",
  ] as const;
  const esc = (v: unknown) => {
    const s = v === null || v === undefined ? "" : String(v);
    if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };
  const lines = [fields.join(",")];
  for (const s of stations) {
    lines.push(fields.map((f) => esc(s[f])).join(","));
  }
  return lines.join("\n") + "\n";
}

/** Pipeline: normalized stations → sorted calendar + alerts payload. */
export function processNormalized(
  stations: NormalizedStation[],
  asOfYmd?: string,
  regulator = "CZ-CTU"
): AlertsPayload {
  const today = asOfYmd ?? todayPrague();
  const enriched = sortStations(enrichNormalized(stations, today));
  return buildAlertsPayload(enriched, today, regulator);
}
