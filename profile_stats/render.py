from __future__ import annotations

from xml.sax.saxutils import escape

from .model import Report


SVG_WIDTH = 495


def render_stats_svg(report: Report, title: str) -> str:
    metrics = (
        ("Active repositories", str(report.stats.active_repositories)),
        ("Stars earned", _compact_number(report.stats.stars)),
        ("Forks earned", _compact_number(report.stats.forks)),
        ("Followers", _compact_number(report.stats.followers)),
        ("Languages", str(report.stats.language_count)),
        ("Code measured", _format_bytes(report.stats.code_bytes)),
    )
    metric_elements: list[str] = []
    for index, (label, value) in enumerate(metrics):
        column = index % 2
        row = index // 2
        x = 24 + column * 235
        y = 101 + row * 42
        metric_elements.append(
            f'<circle cx="{x + 4}" cy="{y - 5}" r="3" fill="#58a6ff"/>'
            f'<text x="{x + 14}" y="{y}" class="label">{escape(label)}</text>'
            f'<text x="{x + 14}" y="{y + 18}" class="value">{escape(value)}</text>'
        )
    safe_title = escape(title)
    safe_username = escape(report.username)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="225" viewBox="0 0 {SVG_WIDTH} 225" role="img" aria-labelledby="stats-title stats-desc">
  <title id="stats-title">{safe_title}</title>
  <desc id="stats-desc">Repository portfolio statistics for {safe_username}</desc>
  <style>
    .title {{ font: 600 18px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #58a6ff; }}
    .subtitle {{ font: 400 12px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #8b949e; }}
    .label {{ font: 400 12px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #8b949e; }}
    .value {{ font: 600 15px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #c9d1d9; }}
  </style>
  <rect x="0.5" y="0.5" width="494" height="224" rx="6" fill="#0d1117" stroke="#30363d"/>
  <text x="24" y="36" class="title">{safe_title}</text>
  <text x="24" y="58" class="subtitle">@{safe_username} · active repository portfolio</text>
  <line x1="24" y1="73" x2="471" y2="73" stroke="#21262d"/>
  {''.join(metric_elements)}
</svg>
"""


def render_languages_svg(report: Report, title: str) -> str:
    safe_title = escape(title)
    safe_username = escape(report.username)
    if not report.languages:
        rows = '<text x="24" y="112" class="empty">No language data for the selected repositories.</text>'
        height = 150
    else:
        row_elements: list[str] = []
        for index, language in enumerate(report.languages):
            y = 98 + index * 36
            bar_width = max(0.0, min(447.0, 447.0 * language.percentage / 100.0))
            row_elements.append(
                f'<circle cx="28" cy="{y - 4}" r="5" fill="{language.color}"/>'
                f'<text x="40" y="{y}" class="language">{escape(language.name)}</text>'
                f'<text x="471" y="{y}" text-anchor="end" class="percentage">{language.percentage:.1f}%</text>'
                f'<rect x="24" y="{y + 9}" width="447" height="7" rx="3.5" fill="#21262d"/>'
                f'<rect x="24" y="{y + 9}" width="{bar_width:.2f}" height="7" rx="3.5" fill="{language.color}"/>'
            )
        rows = "".join(row_elements)
        height = 98 + len(report.languages) * 36 + 15
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{height}" viewBox="0 0 {SVG_WIDTH} {height}" role="img" aria-labelledby="languages-title languages-desc">
  <title id="languages-title">{safe_title}</title>
  <desc id="languages-desc">Languages by GitHub-reported byte count for {safe_username}</desc>
  <style>
    .title {{ font: 600 18px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #58a6ff; }}
    .subtitle, .percentage, .empty {{ font: 400 12px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #8b949e; }}
    .language {{ font: 600 13px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #c9d1d9; }}
  </style>
  <rect x="0.5" y="0.5" width="494" height="{height - 1}" rx="6" fill="#0d1117" stroke="#30363d"/>
  <text x="24" y="36" class="title">{safe_title}</text>
  <text x="24" y="58" class="subtitle">{report.stats.active_repositories} active repositories · {escape(_format_bytes(report.stats.code_bytes))} measured</text>
  <line x1="24" y1="73" x2="471" y2="73" stroke="#21262d"/>
  {rows}
</svg>
"""


def _compact_number(value: int) -> str:
    for threshold, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "k")):
        if value >= threshold:
            amount = value / threshold
            return f"{amount:.1f}{suffix}" if amount < 10 else f"{amount:.0f}{suffix}"
    return str(value)


def _format_bytes(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    amount = float(value)
    unit = units[0]
    for candidate in units:
        unit = candidate
        if amount < 1024 or candidate == units[-1]:
            break
        amount /= 1024
    if unit == "B":
        return f"{int(amount)} {unit}"
    return f"{amount:.1f} {unit}"
