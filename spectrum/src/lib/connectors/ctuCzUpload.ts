/**
 * ČTÚ (Czech Republic) upload adapter — maps CZ portal/export columns
 * onto NormalizedStation. Only connector wired in MVP UI.
 */

import type { ConnectorParseResult, NormalizedStation, RegulatorConnector } from "./types";
import { parseUnixish } from "../domain";

function pick(
  row: Record<string, unknown>,
  keys: string[],
  defaultVal = ""
): string {
  for (const k of keys) {
    if (k in row && row[k] !== null && row[k] !== undefined && String(row[k]).trim() !== "") {
      return String(row[k]).trim();
    }
  }
  return defaultVal;
}

function emptyish(v: unknown): boolean {
  return v === null || v === undefined || String(v).trim() === "";
}

export const ctuCzUploadConnector: RegulatorConnector = {
  id: "CZ-CTU",
  label: "ČTÚ (CZ) — upload CSV/XLSX",

  parseRows(rows: Record<string, unknown>[]): ConnectorParseResult {
    if (!rows.length) {
      throw new Error(
        "Soubor neobsahuje žádné datové řádky. Zkontrolujte export z ČTÚ (CSV/XLSX)."
      );
    }

    const hasValidToColumn = rows.some((r) => "valid_to" in r);
    if (!hasValidToColumn) {
      throw new Error(
        "Chybí povinný sloupec valid_to. Export z ČTÚ musí obsahovat hlavičku valid_to (unix nebo ISO datum)."
      );
    }

    const stations: NormalizedStation[] = [];

    rows.forEach((raw, idx) => {
      const i = idx + 1;
      if (emptyish(raw.valid_to)) {
        throw new Error(
          `Řádek ${i}: chybí hodnota ve sloupci valid_to (povinný pro ČTÚ export).`
        );
      }

      let valid_to: number | null;
      let protected_to: number | null = null;
      let registered_at: number | null = null;
      let updated_at: number | null = null;
      try {
        valid_to = parseUnixish(raw.valid_to);
        if (!emptyish(raw.protected_to)) protected_to = parseUnixish(raw.protected_to);
        if (!emptyish(raw.registered_at)) registered_at = parseUnixish(raw.registered_at);
        if (!emptyish(raw.updated_at)) updated_at = parseUnixish(raw.updated_at);
      } catch (e) {
        throw new Error(`Řádek ${i}: ${(e as Error).message}`);
      }

      if (valid_to === null) {
        throw new Error(
          `Řádek ${i}: valid_to nelze převést na datum (očekáván unix nebo ISO YYYY-MM-DD).`
        );
      }

      const id = pick(raw, ["callsign", "station_id", "id"], `row-${i}`);
      stations.push({
        id,
        name: pick(raw, ["name", "station_name"]),
        valid_to,
        protected_to,
        frequency: pick(raw, ["frequency_mhz", "frequency", "freq"]),
        registered_at,
        updated_at,
        regulator: "CZ-CTU",
        extras: {
          callsign: pick(raw, ["callsign"], id),
        },
      });
    });

    return {
      stations,
      regulator: "CZ-CTU",
      sourceLabel: "ČTÚ upload",
    };
  },
};

/** Default (and only) MVP connector */
export const defaultConnector: RegulatorConnector = ctuCzUploadConnector;
