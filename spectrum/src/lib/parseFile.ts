import * as XLSX from "xlsx";
import { normalizeHeader, parseCsvText, processNormalized, type AlertsPayload } from "./domain";
import { defaultConnector, type RegulatorConnector } from "./connectors";

function assertNonEmptyFile(file: File): void {
  if (!file || file.size === 0) {
    throw new Error("Soubor je prázdný (0 B). Nahrajte export stanic z ČTÚ (CSV/XLSX).");
  }
}

export async function parseUploadedFile(file: File): Promise<Record<string, unknown>[]> {
  assertNonEmptyFile(file);
  const name = file.name.toLowerCase();
  if (name.endsWith(".csv") || file.type === "text/csv" || file.type === "text/plain") {
    const text = await file.text();
    if (!text.trim()) {
      throw new Error("CSV je prázdný. Nahrajte export stanic z ČTÚ s alespoň jedním řádkem.");
    }
    return parseCsvText(text);
  }
  if (name.endsWith(".xlsx") || name.endsWith(".xlsm") || name.endsWith(".xls")) {
    const buf = await file.arrayBuffer();
    return parseXlsxBuffer(buf);
  }
  try {
    const text = await file.text();
    if (text.trim() && (text.includes(",") || text.includes("valid_to"))) {
      return parseCsvText(text);
    }
  } catch {
    /* fall through */
  }
  const buf = await file.arrayBuffer();
  return parseXlsxBuffer(buf);
}

export function parseXlsxBuffer(buf: ArrayBuffer): Record<string, unknown>[] {
  if (!buf || buf.byteLength === 0) {
    throw new Error("XLSX je prázdný. Nahrajte export stanic z ČTÚ.");
  }
  const wb = XLSX.read(buf, { type: "array", cellDates: false });
  const sheetName = wb.SheetNames[0];
  if (!sheetName) throw new Error("XLSX neobsahuje žádný list.");
  const sheet = wb.Sheets[sheetName];
  const aoa = XLSX.utils.sheet_to_json<(string | number | null | undefined)[]>(sheet, {
    header: 1,
    defval: "",
    raw: true,
  });
  if (!aoa.length) throw new Error("XLSX je prázdný (žádné řádky).");
  const headers = (aoa[0] as unknown[]).map((h, i) =>
    h === null || h === undefined || String(h).trim() === ""
      ? `col_${i}`
      : normalizeHeader(String(h))
  );
  if (!headers.some((h) => h === "valid_to")) {
    throw new Error(
      "V souboru chybí datum konce platnosti. V exportu ČTÚ hledejte sloupec s koncem platnosti (někdy valid_to)."
    );
  }
  const rows: Record<string, unknown>[] = [];
  for (let r = 1; r < aoa.length; r++) {
    const values = aoa[r] as unknown[];
    if (!values || values.every((v) => v === null || v === undefined || String(v).trim() === "")) {
      continue;
    }
    const row: Record<string, unknown> = {};
    headers.forEach((h, j) => {
      row[h] = values[j] ?? "";
    });
    rows.push(row);
  }
  if (!rows.length) {
    throw new Error("XLSX má jen hlavičku — chybí datové řádky stanic.");
  }
  return rows;
}

export async function loadSampleCsv(): Promise<Record<string, unknown>[]> {
  const res = await fetch("/sample_stations.csv");
  if (!res.ok) throw new Error("Nepodařilo se načíst ukázková data");
  const text = await res.text();
  return parseCsvText(text);
}

/** Rows → connector normalize → calendar/alerts (CZ upload adapter by default). */
export function rowsToAlerts(
  rows: Record<string, unknown>[],
  connector: RegulatorConnector = defaultConnector,
  asOfYmd?: string
): AlertsPayload {
  const parsed = connector.parseRows(rows);
  return processNormalized(parsed.stations, asOfYmd, parsed.regulator);
}
