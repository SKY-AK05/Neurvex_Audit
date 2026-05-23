/** Escape text for safe HTML insertion */
function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Convert legacy plain-text email bodies to HTML for TipTap.
 * Already-HTML content is returned unchanged.
 */
export function normalizeEmailHtml(content) {
  const raw = (content || "").trim();
  if (!raw) return "";

  if (/<\/?[a-z][\s\S]*>/i.test(raw)) return raw;

  const parts = [];
  let paragraphLines = [];

  function flushParagraph() {
    if (!paragraphLines.length) return;
    const firstLine = paragraphLines[0].trim();
    if (firstLine.startsWith("● ")) {
      const title = firstLine.slice(2);
      const contentLines = [];
      for (let i = 1; i < paragraphLines.length; i++) {
        const line = paragraphLines[i];
        if (line.startsWith("   ")) {
          contentLines.push(line.slice(3));
        } else {
          contentLines.push(line.trim());
        }
      }
      const interpretationText = contentLines.join(" ");
      parts.push(
        `<div style="margin:0 0 1.25em 0;">` +
        `<p style="margin:0;text-indent:-1.25em;padding-left:1.25em;line-height:1.6;">` +
        `● <strong>${escapeHtml(title)}</strong>` +
        `</p>` +
        (interpretationText ? `<p style="margin:0.35em 0 0 1.25em;line-height:1.6;">${escapeHtml(interpretationText)}</p>` : "") +
        `</div>`
      );
      paragraphLines = [];
      return;
    }

    const inner = paragraphLines
      .map((line) => {
        const t = line.trim();
        if (t.startsWith("● ")) {
          return `● <strong>${escapeHtml(t.slice(2))}</strong>`;
        }
        if (line.startsWith("   ")) {
          return escapeHtml(line.trim());
        }
        return escapeHtml(line);
      })
      .join("<br>");
    parts.push(`<p>${inner}</p>`);
    paragraphLines = [];
  }

  for (const line of raw.split("\n")) {
    const trimmed = line.trim();
    if (/^=+$/.test(trimmed)) {
      flushParagraph();
      parts.push("<hr>");
      continue;
    }
    if (trimmed === "OVERALL AUDIT SUMMARY") {
      flushParagraph();
      parts.push("<h3>Overall Audit Summary</h3>");
      continue;
    }
    if (trimmed === "SYNOPSIS:") {
      flushParagraph();
      parts.push("<h3>Synopsis</h3>");
      continue;
    }
    if (trimmed === "") {
      flushParagraph();
      continue;
    }
    paragraphLines.push(line);
  }
  flushParagraph();

  return parts.join("");
}
