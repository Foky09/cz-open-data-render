import type { AlertsPayload } from "./domain";

const KEY = "spectrumdeadline:lastResult";

export function saveResult(payload: AlertsPayload): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(payload));
  } catch {
    /* quota / private mode */
  }
}

export function loadResult(): AlertsPayload | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw) as AlertsPayload;
  } catch {
    return null;
  }
}

export function clearResult(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
