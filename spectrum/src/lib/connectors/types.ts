/**
 * Thin regulator connector — normalize station exports into a common shape.
 * Calendar/alerts core consumes NormalizedStation only (no ČTÚ field names).
 * Future: DE BNetzA / AT / IT adapters plug in here; UI stays CZ-only for MVP.
 */

export interface NormalizedStation {
  /** Stable station id (callsign / licence id / row-N) */
  id: string;
  name: string;
  /** Unix seconds (UTC-based instant); null if regulator has no validity end */
  valid_to: number | null;
  /** Unix seconds; optional protection window end */
  protected_to: number | null;
  /** Display frequency if available */
  frequency: string;
  /** Optional passthrough timestamps */
  registered_at: number | null;
  updated_at: number | null;
  /** Original regulator country / code */
  regulator: string;
  /** Raw extras for export/debug (never used by bucket logic) */
  extras?: Record<string, unknown>;
}

export interface ConnectorParseResult {
  stations: NormalizedStation[];
  regulator: string;
  sourceLabel: string;
}

export interface RegulatorConnector {
  /** Short code, e.g. "CZ-CTU" */
  id: string;
  /** Human label */
  label: string;
  /** Parse already-tabular rows (headers normalized by caller or adapter) */
  parseRows(rows: Record<string, unknown>[]): ConnectorParseResult;
}
