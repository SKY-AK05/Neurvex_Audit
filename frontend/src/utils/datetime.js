/** Indian Standard Time (UTC+5:30) — used across the app for display and date logic. */
export const IST_TIMEZONE = "Asia/Kolkata";

const LOCALE = "en-IN";

/** e.g. 29 May 2026, 3:45 pm */
export function formatDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(LOCALE, {
    timeZone: IST_TIMEZONE,
    dateStyle: "medium",
    timeStyle: "short",
  });
}

/** e.g. 29 May 2026 */
export function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(LOCALE, {
    timeZone: IST_TIMEZONE,
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

/** e.g. 29 May (no year) */
export function formatDateShort(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(LOCALE, {
    timeZone: IST_TIMEZONE,
    day: "numeric",
    month: "short",
  });
}

/** yyyy-mm-dd in IST — for date-range filters */
export function toISTDateString(isoOrDate) {
  if (!isoOrDate) return "";
  return new Intl.DateTimeFormat("en-CA", { timeZone: IST_TIMEZONE }).format(
    new Date(isoOrDate)
  );
}

/** Start of calendar week (Sunday 00:00) in IST, as UTC instant */
export function startOfISTWeek(instant = new Date()) {
  let cursor = new Date(instant);
  for (let i = 0; i < 8; i++) {
    const wd = new Intl.DateTimeFormat("en-US", {
      timeZone: IST_TIMEZONE,
      weekday: "short",
    }).format(cursor);
    if (wd === "Sun") {
      const [y, m, d] = toISTDateString(cursor).split("-").map(Number);
      return istWallClockToUtc(y, m, d, 0, 0, 0);
    }
    cursor = new Date(cursor.getTime() - 24 * 60 * 60 * 1000);
  }
  return instant;
}

/** Month key and label in IST for charts */
export function getISTMonthKey(iso) {
  const d = new Date(iso);
  const year = new Intl.DateTimeFormat("en-CA", { timeZone: IST_TIMEZONE, year: "numeric" }).format(d);
  const month = new Intl.DateTimeFormat("en-CA", { timeZone: IST_TIMEZONE, month: "2-digit" }).format(d);
  const label = new Intl.DateTimeFormat(LOCALE, {
    timeZone: IST_TIMEZONE,
    month: "short",
    year: "numeric",
  }).format(d);
  return { key: `${year}-${month}`, label };
}

/** Today yyyy-mm-dd in IST for filenames */
export function todayISTDateString() {
  return toISTDateString(new Date());
}

function istWallClockToUtc(year, month, day, hour = 0, minute = 0, second = 0) {
  const utcMs = Date.UTC(year, month - 1, day, hour, minute, second);
  return new Date(utcMs - 5.5 * 60 * 60 * 1000);
}
