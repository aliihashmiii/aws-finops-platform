/* FinOps AI Control Plane — React 18 client without a build step.
 * Every figure on screen is read from the API (or the generated static fixtures on GitHub Pages).
 * Derived numbers (deltas, health score, budget status, forecast crossover) are computed here
 * from those responses and never typed in. */
const { useEffect, useMemo, useRef, useState, useCallback } = React;
const h = React.createElement;
const Fragment = React.Fragment;

// Edit to personalise the workspace greeting and profile footer.
const PROFILE = { name: 'Ali Hashmi', role: 'FinOps Practitioner' };

/* ---------------------------------------------------------------- data access */
function staticPath(path) {
  const [pathname, query = ''] = path.split('?');
  const filename = pathname.replace(/^\/api\//, '').replaceAll('/', '-') + '.json';
  const staticName = pathname === '/api/recommendations' && query.includes('platform=aws') ? 'recommendations-aws.json' : filename;
  return 'demo-api/' + staticName;
}

let STATIC_MODE = false;
async function fetchJSON(path, options) {
  let live = null;
  try { live = await fetch(path, options); } catch (e) { live = null; }
  if (live && live.ok) {
    const type = live.headers.get('content-type') || '';
    if (type.includes('application/json')) return live.json();
  }
  if (options && options.method && options.method !== 'GET') throw new Error('Saving needs the FastAPI backend. This static site is a read-only demo.');
  const fallback = await fetch(staticPath(path));
  if (!fallback.ok) throw new Error('The API is unavailable and no static demo fixture exists for ' + path + '.');
  STATIC_MODE = true;
  return fallback.json();
}
const loadAll = (paths) => Promise.all(paths.map((p) => fetchJSON(p)));

/* ---------------------------------------------------------------- formatting */
const money = (v) => '$' + Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
const money2 = (v) => '$' + Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const compact = (v) => { const n = Number(v || 0); if (Math.abs(n) >= 1e6) return '$' + (n / 1e6).toFixed(1) + 'M'; if (Math.abs(n) >= 1e3) return '$' + (n / 1e3).toFixed(n >= 1e5 ? 0 : 1) + 'K'; return '$' + n.toFixed(0); };
const number = (v) => Number(v || 0).toLocaleString();
const tokens = (v) => { const n = Number(v || 0); if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B'; if (n >= 1e6) return (n / 1e6).toFixed(n >= 1e7 ? 0 : 1) + 'M'; if (n >= 1e3) return (n / 1e3).toFixed(0) + 'K'; return number(n); };
const pct = (v, d = 1) => Number(v || 0).toFixed(d) + '%';
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const periodLabel = (p, long) => { if (!p) return ''; const [y, m] = p.split('-').map(Number); return long ? `${MONTHS[m - 1]} ${y}` : `${MONTHS[m - 1]} '${String(y).slice(2)}`; };
const addMonths = (p, n) => { const [y, m] = p.split('-').map(Number); const d = new Date(Date.UTC(y, m - 1 + n, 1)); return d.getUTCFullYear() + '-' + String(d.getUTCMonth() + 1).padStart(2, '0'); };
const change = (series) => { if (!series || series.length < 2) return null; const a = series[series.length - 2], b = series[series.length - 1]; return a ? (b - a) / a * 100 : null; };
const sum = (xs) => xs.reduce((a, b) => a + Number(b || 0), 0);

/* ---------------------------------------------------------------- icons */
const ICONS = {
  home: 'M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z',
  chart: 'M4 20V10M10 20V4M16 20v-7M2 20h20',
  zap: 'M13 2 3 14h9l-1 8 10-12h-9z',
  cube: 'M12 2 3 7v10l9 5 9-5V7zM3 7l9 5 9-5M12 12v10',
  sparkles: 'M12 3l1.8 4.7 4.7 1.8-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8zM19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z',
  bell: 'M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.9 1.9 0 0 0 3.4 0',
  settings: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z',
  search: 'M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.3-4.3',
  sun: 'M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zM12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4',
  moon: 'M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z',
  calendar: 'M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zM16 2v4M8 2v4M3 10h18',
  wallet: 'M3 7a2 2 0 0 1 2-2h13v4M3 7v11a2 2 0 0 0 2 2h15V9H5a2 2 0 0 1-2-2zM16 14.5h.01',
  leaf: 'M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10zM2 21c0-3 1.9-5.4 5.2-6',
  cloud: 'M17.5 19H9a7 7 0 1 1 6.7-9h1.8a4.5 4.5 0 1 1 0 9z',
  cpu: 'M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2M6 4h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zM9 9h6v6H9z',
  heart: 'M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4 3 5.5l7 7z',
  arrowRight: 'M5 12h14M12 5l7 7-7 7',
  up: 'M12 19V5M5 12l7-7 7 7',
  down: 'M12 5v14M19 12l-7 7-7-7',
  server: 'M4 3h16a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM4 13h16a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1zM7 7h.01M7 17h.01',
  database: 'M12 8c4.4 0 8-1.3 8-3s-3.6-3-8-3-8 1.3-8 3 3.6 3 8 3zM4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3',
  disk: 'M22 12H2M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.1zM6 16h.01M10 16h.01',
  layers: 'M12 2 2 7l10 5 10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
  refresh: 'M21 12a9 9 0 1 1-2.6-6.4L21 8M21 3v5h-5',
  menu: 'M3 6h18M3 12h18M3 18h18',
  x: 'M18 6 6 18M6 6l12 12',
  check: 'M20 6 9 17l-5-5',
  alert: 'M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z',
  camera: 'M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3zM12 16a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  globe: 'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM2 12h20M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20',
  trend: 'M22 7 13.5 15.5 8.5 10.5 2 17M16 7h6v6',
  book: 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20V2H6.5A2.5 2.5 0 0 0 4 4.5zM4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5',
  shield: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  gauge: 'M12 14l4-4M3.3 19a10 10 0 1 1 17.4 0M12 14a1 1 0 1 0 0 .01',
};
function Icon({ name, size = 20, stroke = 1.8, className }) {
  return h('svg', { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: stroke, strokeLinecap: 'round', strokeLinejoin: 'round', className, 'aria-hidden': 'true' }, h('path', { d: ICONS[name] || '' }));
}
function Logo() {
  return h('svg', { width: 44, height: 44, viewBox: '0 0 48 48', 'aria-hidden': 'true' },
    h('defs', null, h('linearGradient', { id: 'lg', x1: 0, y1: 1, x2: 1, y2: 0 }, h('stop', { offset: 0, stopColor: '#0f5b37' }), h('stop', { offset: 1, stopColor: '#5fb48a' }))),
    h('path', { d: 'M8 40C8 20 20 8 42 6c0 22-12 34-32 34z', fill: 'url(#lg)' }),
    h('path', { d: 'M10 38C18 28 26 20 36 12', stroke: '#f2b632', strokeWidth: 3.2, strokeLinecap: 'round', fill: 'none' }));
}

/* ---------------------------------------------------------------- domain vocabulary */
const CATEGORY = {
  'idle-instance': { label: 'Idle EC2 instances', icon: 'server' },
  'stopped-instance': { label: 'Stopped EC2 instances', icon: 'server' },
  'unattached-volume': { label: 'Unattached EBS volumes', icon: 'disk' },
  'old-snapshot': { label: 'Aged EBS snapshots', icon: 'camera' },
  'unused-eip': { label: 'Unassociated Elastic IPs', icon: 'globe' },
  'idle-rds': { label: 'Underused RDS instances', icon: 'database' },
  'workload-rightsizing': { label: 'Rightsize Kubernetes workloads', icon: 'cube' },
  'node-consolidation': { label: 'Consolidate Kubernetes nodes', icon: 'layers' },
  'replica-efficiency': { label: 'Review replica floors', icon: 'layers' },
  'model-overprovisioning': { label: 'Route simple tasks to lower-cost models', icon: 'sparkles' },
  'cache-opportunity': { label: 'Cache repeat AI requests', icon: 'sparkles' },
  'excessive-input': { label: 'Trim AI input context', icon: 'sparkles' },
  'output-variance': { label: 'Constrain AI output length', icon: 'sparkles' },
};
const catLabel = (c) => (CATEGORY[c] && CATEGORY[c].label) || c.replace(/-/g, ' ');
const catIcon = (c) => (CATEGORY[c] && CATEGORY[c].icon) || 'zap';
const effortOf = (risk) => ({ Low: 'low', Medium: 'medium', High: 'high' }[risk] || 'medium');
const PLATFORM_COLORS = { AWS: '#f2711c', Kubernetes: '#1f7a4d', AI: '#7c5cd6' };

function groupByCategory(findings) {
  const map = new Map();
  findings.filter((f) => f.estimated_monthly_savings > 0).forEach((f) => {
    const g = map.get(f.category) || { category: f.category, platform: f.platform, count: 0, savings: 0, risks: [] };
    g.count += 1; g.savings += f.estimated_monthly_savings; g.risks.push(f.risk); map.set(f.category, g);
  });
  return [...map.values()].map((g) => ({ ...g, effort: g.risks.includes('High') ? 'High' : g.risks.includes('Medium') ? 'Medium' : 'Low' })).sort((a, b) => b.savings - a.savings);
}

/* ---------------------------------------------------------------- hooks */
function useWidth() {
  const ref = useRef(null);
  const [width, setWidth] = useState(600);
  useEffect(() => {
    if (!ref.current) return undefined;
    const update = () => ref.current && setWidth(ref.current.clientWidth || 600);
    update();
    if (typeof ResizeObserver === 'undefined') { window.addEventListener('resize', update); return () => window.removeEventListener('resize', update); }
    const ro = new ResizeObserver(update); ro.observe(ref.current); return () => ro.disconnect();
  }, []);
  return [ref, width];
}

/* ---------------------------------------------------------------- charts */
function niceMax(v) { if (v <= 0) return 1; const p = Math.pow(10, Math.floor(Math.log10(v))); const n = v / p; return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * p; }

function LineChart({ labels, series, height = 230, yFormat = compact, refLine, highlight }) {
  const [ref, width] = useWidth();
  const [hover, setHover] = useState(null);
  const padL = 46, padR = 14, padT = 14, padB = 28;
  const all = series.flatMap((s) => s.values.filter((v) => v != null)).concat(refLine ? [refLine.value] : []);
  const max = niceMax(Math.max(...all, 1) * 1.08);
  const innerW = Math.max(10, width - padL - padR), innerH = height - padT - padB;
  const x = (i) => padL + (labels.length > 1 ? i * innerW / (labels.length - 1) : innerW / 2);
  const y = (v) => padT + innerH - (v / max) * innerH;
  const ticks = [0, .25, .5, .75, 1].map((t) => t * max);
  const every = Math.max(1, Math.ceil(labels.length / Math.max(2, Math.floor(innerW / 70))));
  const pathOf = (vals, smooth) => {
    const pts = vals.map((v, i) => v == null ? null : [x(i), y(v)]).filter(Boolean);
    if (!pts.length) return '';
    if (!smooth || pts.length < 3) return 'M' + pts.map((p) => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join('L');
    let d = 'M' + pts[0][0].toFixed(1) + ',' + pts[0][1].toFixed(1);
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2, t = 0.18;
      d += `C${(p1[0] + (p2[0] - p0[0]) * t).toFixed(1)},${(p1[1] + (p2[1] - p0[1]) * t).toFixed(1)} ${(p2[0] - (p3[0] - p1[0]) * t).toFixed(1)},${(p2[1] - (p3[1] - p1[1]) * t).toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
    }
    return d;
  };
  const onMove = (e) => { const r = e.currentTarget.getBoundingClientRect(); const px = e.clientX - r.left; const i = Math.round((px - padL) / (innerW / Math.max(1, labels.length - 1))); setHover(Math.max(0, Math.min(labels.length - 1, i))); };
  const hoverSeries = hover == null ? null : series.find((s) => s.values[hover] != null);
  const gradId = useMemo(() => 'g' + Math.random().toString(36).slice(2, 8), []);
  return h('div', { className: 'chart-wrap', ref },
    h('svg', { width, height, onMouseMove: onMove, onMouseLeave: () => setHover(null), role: 'img', 'aria-label': series.map((s) => s.name).join(', ') + ' chart' },
      h('defs', null, series.filter((s) => s.fill).map((s, k) => h('linearGradient', { key: k, id: gradId + k, x1: 0, y1: 0, x2: 0, y2: 1 }, h('stop', { offset: 0, stopColor: s.color, stopOpacity: .28 }), h('stop', { offset: 1, stopColor: s.color, stopOpacity: .02 })))),
      ticks.map((t, i) => h('g', { key: 't' + i }, h('line', { className: 'grid-line', x1: padL, x2: width - padR, y1: y(t), y2: y(t) }), h('text', { className: 'axis-text', x: padL - 8, y: y(t) + 4, textAnchor: 'end' }, yFormat(t)))),
      refLine && h('g', null, h('line', { x1: padL, x2: width - padR, y1: y(refLine.value), y2: y(refLine.value), stroke: refLine.color, strokeDasharray: '6 5', strokeWidth: 1.6 }), h('text', { className: 'axis-text', x: padL + 6, y: y(refLine.value) - 7, textAnchor: 'start', style: { fill: refLine.color, fontWeight: 600 } }, refLine.label)),
      series.filter((s) => s.fill).map((s, k) => { const pts = s.values.map((v, i) => v == null ? null : [x(i), y(v)]).filter(Boolean); if (pts.length < 2) return null; const d = pathOf(s.values, s.smooth) + `L${pts[pts.length - 1][0]},${y(0)}L${pts[0][0]},${y(0)}Z`; return h('path', { key: 'a' + k, d, fill: `url(#${gradId}${k})` }); }),
      series.map((s, k) => h('path', { key: 'l' + k, d: pathOf(s.values, s.smooth), fill: 'none', stroke: s.color, strokeWidth: s.width || 2.4, strokeDasharray: s.dashed ? '6 5' : undefined, strokeLinecap: 'round', strokeLinejoin: 'round', opacity: s.opacity || 1 })),
      labels.map((l, i) => { const last = labels.length - 1; const show = i === last || (i % every === 0 && last - i >= Math.max(1, every * 0.75)); return show ? h('text', { key: 'x' + i, className: 'axis-text', x: x(i), y: height - 6, textAnchor: i === last && labels.length > 1 ? 'end' : i === 0 ? 'start' : 'middle' }, l) : null; }),
      highlight != null && h('circle', { cx: x(highlight.index), cy: y(highlight.value), r: 5, fill: highlight.color, stroke: 'var(--surface)', strokeWidth: 2 }),
      hover != null && h('line', { x1: x(hover), x2: x(hover), y1: padT, y2: padT + innerH, stroke: 'var(--line-strong)', strokeDasharray: '3 3' }),
      hover != null && series.map((s, k) => s.values[hover] == null ? null : h('circle', { key: 'c' + k, cx: x(hover), cy: y(s.values[hover]), r: 4.5, fill: s.color, stroke: 'var(--surface)', strokeWidth: 2 }))),
    hover != null && hoverSeries && h('div', { className: 'tooltip gf', style: { left: x(hover), top: y(Math.max(...series.map((s) => s.values[hover] == null ? 0 : s.values[hover]))) } }, h('span', { className: 'tt-title' }, labels[hover]), series.filter((s) => s.values[hover] != null).map((s) => h('div', { className: 'tt-row', key: s.name }, h('i', { style: { background: s.color } }), s.name, h('b', { className: 'num' }, money(s.values[hover]))))));
}

function Sparkline({ values, color = 'var(--green)', width = 96, height = 42 }) {
  const vals = (values || []).map(Number);
  if (vals.length < 2) return null;
  const min = Math.min(...vals), max = Math.max(...vals), r = max - min || 1;
  const pts = vals.map((v, i) => [i * width / (vals.length - 1), height - 4 - (v - min) / r * (height - 8)]);
  const id = 'sp' + Math.abs(Math.round(vals[0] * 7 + vals.length)) + color.length;
  return h('svg', { width, height, className: 'kpi-spark', 'aria-hidden': 'true' },
    h('defs', null, h('linearGradient', { id, x1: 0, y1: 0, x2: 0, y2: 1 }, h('stop', { offset: 0, stopColor: color, stopOpacity: .25 }), h('stop', { offset: 1, stopColor: color, stopOpacity: 0 }))),
    h('path', { d: 'M' + pts.map((p) => p.join(',')).join('L') + `L${width},${height}L0,${height}Z`, fill: `url(#${id})` }),
    h('path', { d: 'M' + pts.map((p) => p.join(',')).join('L'), fill: 'none', stroke: color, strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round' }));
}

function AreaSpark({ values, color = 'var(--green)' }) {
  const vals = (values || []).map(Number);
  if (vals.length < 2) return null;
  const W = 300, H = 72, min = Math.min(...vals) * 0.97, max = Math.max(...vals), r = max - min || 1;
  const pts = vals.map((v, i) => [i * W / (vals.length - 1), H - 4 - (v - min) / r * (H - 10)]);
  const line = 'M' + pts.map((p) => p.map((n) => n.toFixed(1)).join(',')).join('L');
  return h('svg', { className: 'area-spark', viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: 'none', role: 'img', 'aria-label': 'Monthly AI spend trend' },
    h('defs', null, h('linearGradient', { id: 'areaSpark', x1: 0, y1: 0, x2: 0, y2: 1 }, h('stop', { offset: 0, stopColor: color, stopOpacity: .28 }), h('stop', { offset: 1, stopColor: color, stopOpacity: 0 }))),
    h('path', { d: line + `L${W},${H}L0,${H}Z`, fill: 'url(#areaSpark)' }),
    h('path', { d: line, fill: 'none', stroke: color, strokeWidth: 2.4, vectorEffect: 'non-scaling-stroke', strokeLinejoin: 'round' }));
}

function Ring({ value, size = 104, stroke = 11, color = 'var(--green)', label, sub }) {
  const r = (size - stroke) / 2, c = 2 * Math.PI * r, v = Math.max(0, Math.min(100, Number(value || 0)));
  return h('div', { style: { position: 'relative', width: size, height: size, flexShrink: 0 } },
    h('svg', { width: size, height: size, style: { transform: 'rotate(-90deg)' } }, h('circle', { cx: size / 2, cy: size / 2, r, fill: 'none', stroke: 'var(--surface-3)', strokeWidth: stroke }), h('circle', { cx: size / 2, cy: size / 2, r, fill: 'none', stroke: color, strokeWidth: stroke, strokeLinecap: 'round', strokeDasharray: `${c * v / 100} ${c}` })),
    h('div', { className: 'donut-center' }, h('strong', { className: 'num', style: { fontSize: size > 110 ? 30 : 24 } }, label), sub && h('span', null, sub)));
}

function Donut({ items, size = 168, stroke = 30, centerLabel, centerSub }) {
  const total = sum(items.map((i) => i.value)) || 1;
  const r = (size - stroke) / 2, c = 2 * Math.PI * r;
  let offset = 0;
  return h('div', { style: { position: 'relative', width: size, height: size, flexShrink: 0 } },
    h('svg', { width: size, height: size, style: { transform: 'rotate(-90deg)' }, role: 'img', 'aria-label': 'Spend by platform' }, items.map((it, i) => { const len = c * it.value / total; const el = h('circle', { key: i, cx: size / 2, cy: size / 2, r, fill: 'none', stroke: it.color, strokeWidth: stroke, strokeDasharray: `${Math.max(0, len - 2)} ${c}`, strokeDashoffset: -offset }); offset += len; return el; })),
    h('div', { className: 'donut-center' }, h('strong', { className: 'num' }, centerLabel), h('span', null, centerSub)));
}

/* ---------------------------------------------------------------- Grafana-style panel kit
 * Thresholds follow Grafana semantics: an ascending list of steps; a value takes the colour of
 * the last step whose `value` is <= it. That lets "too low" and "too high" both be warnings. */
const T = {
  good: 'var(--green)', warn: 'var(--amber)', bad: 'var(--red)', info: 'var(--blue)',
  higherIsBetter: (warnAt, okAt) => [{ value: -Infinity, color: 'var(--red)' }, { value: warnAt, color: 'var(--amber)' }, { value: okAt, color: 'var(--green)' }],
  lowerIsBetter: (warnAt, badAt) => [{ value: -Infinity, color: 'var(--green)' }, { value: warnAt, color: 'var(--amber)' }, { value: badAt, color: 'var(--red)' }],
  band: (low, okLow, okHigh) => [{ value: -Infinity, color: 'var(--red)' }, { value: low, color: 'var(--amber)' }, { value: okLow, color: 'var(--green)' }, { value: okHigh, color: 'var(--amber)' }],
};
const thresholdColor = (v, steps) => { let c = steps && steps.length ? steps[0].color : 'var(--green)'; (steps || []).forEach((s) => { if (v >= s.value) c = s.color; }); return c; };
const SERIES_COLORS = ['#1f7a4d', '#f2711c', '#7c5cd6', '#2a9d8f', '#f2b632', '#3b6fd8', '#d64545', '#5fb48a'];

function Panel({ title, info, right, children, span = 4, className = '', minHeight }) {
  return h('section', { className: `panel s${span} ${className}`, style: minHeight ? { minHeight } : null },
    h('header', { className: 'panel-head' }, h('h3', null, title), info && h('span', { className: 'panel-info', title: info, 'aria-label': info }, 'i'), right && h('div', { className: 'panel-right' }, right)),
    h('div', { className: 'panel-body' }, children));
}

const polar = (cx, cy, r, deg) => { const a = (deg - 90) * Math.PI / 180; return [cx + r * Math.cos(a), cy + r * Math.sin(a)]; };
const arc = (cx, cy, r, a0, a1) => { const [x0, y0] = polar(cx, cy, r, a0), [x1, y1] = polar(cx, cy, r, a1); return `M${x0.toFixed(2)},${y0.toFixed(2)} A${r},${r} 0 ${a1 - a0 > 180 ? 1 : 0} 1 ${x1.toFixed(2)},${y1.toFixed(2)}`; };

function Gauge({ value, min = 0, max = 100, thresholds, unit = '%', decimals = 0, label }) {
  const v = Number(value || 0), clamped = Math.max(min, Math.min(max, v));
  const START = -120, SWEEP = 240, toAngle = (x) => START + (Math.max(min, Math.min(max, x)) - min) / (max - min || 1) * SWEEP;
  const color = thresholdColor(v, thresholds);
  const bands = (thresholds || []).map((s, i, arr) => ({ from: Math.max(min, s.value === -Infinity ? min : s.value), to: i + 1 < arr.length ? Math.min(max, arr[i + 1].value) : max, color: s.color })).filter((b) => b.to > b.from);
  return h('div', { className: 'gauge' }, h('svg', { viewBox: '0 0 200 160', role: 'img', 'aria-label': `${label || 'Gauge'}: ${v.toFixed(decimals)}${unit}` },
    bands.map((b, i) => h('path', { key: i, d: arc(100, 100, 86, toAngle(b.from) + 0.6, toAngle(b.to) - 0.6), stroke: b.color, strokeWidth: 4, fill: 'none', opacity: .9 })),
    h('path', { d: arc(100, 100, 72, START, START + SWEEP), stroke: 'var(--surface-3)', strokeWidth: 16, fill: 'none', strokeLinecap: 'round' }),
    clamped > min && h('path', { d: arc(100, 100, 72, START, toAngle(clamped)), stroke: color, strokeWidth: 16, fill: 'none', strokeLinecap: 'round' }),
    h('text', { x: 100, y: 104, textAnchor: 'middle', className: 'gauge-value', style: { fill: color } }, v.toFixed(decimals) + unit),
    h('text', { x: 100, y: 124, textAnchor: 'middle', className: 'gauge-label' }, label || ''),
    h('text', { x: polar(100, 100, 72, START)[0] - 4, y: 157, textAnchor: 'middle', className: 'gauge-minmax' }, min + unit),
    h('text', { x: polar(100, 100, 72, START + SWEEP)[0] + 4, y: 157, textAnchor: 'middle', className: 'gauge-minmax' }, max + unit)));
}

function BarGauge({ items, max, thresholds, mode = 'lcd', format = (v) => v.toFixed(0) + '%', cells = 28 }) {
  const top = max != null ? max : Math.max(...items.map((i) => i.value), 1);
  return h('div', { className: 'bar-gauges' }, items.map((it) => {
    const ratio = Math.max(0, Math.min(1, it.value / top)), color = thresholdColor(it.value, thresholds);
    return h('div', { className: 'bar-gauge', key: it.key || it.label, title: `${it.label}: ${format(it.value)}` },
      h('div', { className: 'bg-label' }, it.label, it.sub && h('span', null, it.sub)),
      mode === 'lcd'
        ? h('div', { className: 'bg-lcd' }, Array.from({ length: cells }, (_, i) => { const cellValue = (i + 0.5) / cells * top; const on = (i + 0.5) / cells <= ratio; return h('i', { key: i, style: { background: on ? thresholdColor(cellValue, thresholds) : undefined, opacity: on ? 1 : undefined } }); }))
        : h('div', { className: 'bg-track' }, h('div', { className: 'bg-fill', style: { width: ratio * 100 + '%', background: thresholds ? `linear-gradient(90deg, ${thresholds.map((s) => s.color).join(', ')})` : color, backgroundSize: ratio ? (100 / ratio) + '% 100%' : '100% 100%' } })),
      h('div', { className: 'bg-value num', style: { color } }, format(it.value)));
  }));
}

function StatPanel({ value, display, spark, thresholds, sub, color }) {
  const c = color || (thresholds ? thresholdColor(value, thresholds) : 'var(--green)');
  return h('div', { className: 'stat-panel' }, h('div', { className: 'stat-value num', style: { color: c } }, display != null ? display : value), sub && h('div', { className: 'stat-sub' }, sub), spark && spark.length > 1 && h('div', { className: 'stat-spark' }, h(AreaSpark, { values: spark, color: c })));
}

function BarChart({ labels, series, stacked = false, height = 240, yFormat = compact, valueFormat = money }) {
  const [ref, width] = useWidth();
  const [hover, setHover] = useState(null);
  const padL = 50, padR = 10, padT = 10, padB = 28, innerW = Math.max(10, width - padL - padR), innerH = height - padT - padB;
  const totals = labels.map((_, i) => stacked ? sum(series.map((s) => s.values[i])) : Math.max(...series.map((s) => Number(s.values[i] || 0))));
  const max = niceMax(Math.max(...totals, 1) * 1.05), y = (v) => padT + innerH - v / max * innerH;
  const slot = innerW / Math.max(1, labels.length), groupW = slot * 0.68, barW = stacked ? groupW : groupW / series.length;
  const every = Math.max(1, Math.ceil(labels.length / Math.max(2, Math.floor(innerW / 60))));
  return h('div', { className: 'chart-wrap', ref },
    h('svg', { width, height, role: 'img', 'aria-label': series.map((s) => s.name).join(', ') + ' bar chart', onMouseLeave: () => setHover(null) },
      [0, .25, .5, .75, 1].map((t, i) => h('g', { key: i }, h('line', { className: 'grid-line', x1: padL, x2: width - padR, y1: y(t * max), y2: y(t * max) }), h('text', { className: 'axis-text', x: padL - 8, y: y(t * max) + 4, textAnchor: 'end' }, yFormat(t * max)))),
      labels.map((l, i) => { const x0 = padL + i * slot + (slot - groupW) / 2; let acc = 0; return h('g', { key: i, onMouseEnter: () => setHover(i) },
        h('rect', { x: padL + i * slot, y: padT, width: slot, height: innerH, fill: hover === i ? 'var(--surface-2)' : 'transparent' }),
        series.map((s, k) => { const v = Number(s.values[i] || 0); const top = stacked ? y(acc + v) : y(v); const hgt = stacked ? y(acc) - y(acc + v) : y(0) - y(v); const bx = stacked ? x0 : x0 + k * barW; acc += v; return h('rect', { key: k, x: bx + (stacked ? 0 : 1), y: top, width: Math.max(1, barW - (stacked ? 0 : 2)), height: Math.max(0, hgt - (stacked && k < series.length - 1 ? 0 : 0)), rx: stacked ? (k === series.length - 1 ? 3 : 0) : 3, fill: s.color, opacity: hover == null || hover === i ? 1 : .55 }); }),
        (i % every === 0) && h('text', { className: 'axis-text', x: padL + i * slot + slot / 2, y: height - 8, textAnchor: 'middle' }, l)); })),
    hover != null && h('div', { className: 'tooltip gf', style: { left: padL + hover * slot + slot / 2, top: y(totals[hover]) } },
      h('span', { className: 'tt-title' }, labels[hover]), series.map((s) => h('div', { className: 'tt-row', key: s.name }, h('i', { style: { background: s.color } }), s.name, h('b', { className: 'num' }, valueFormat(s.values[hover])))), stacked && h('div', { className: 'tt-row total' }, 'Total', h('b', { className: 'num' }, valueFormat(totals[hover])))));
}

function HBarChart({ items, format = money, color = 'var(--green)', thresholds }) {
  const max = Math.max(...items.map((i) => i.value), 1);
  return h('div', { className: 'hbars' }, items.map((it, i) => h('div', { className: 'hbar', key: it.label + i, title: `${it.label}: ${format(it.value)}` },
    h('div', { className: 'hbar-label' }, it.label),
    h('div', { className: 'hbar-track' }, h('div', { className: 'hbar-fill', style: { width: Math.max(1.5, it.value / max * 100) + '%', background: it.color || (thresholds ? thresholdColor(it.value, thresholds) : color) } })),
    h('div', { className: 'hbar-value num' }, format(it.value)))));
}

function LegendTable({ series, format = money }) {
  const stats = (vals) => { const v = vals.filter((x) => x != null).map(Number); return v.length ? { mean: sum(v) / v.length, max: Math.max(...v), last: v[v.length - 1] } : { mean: 0, max: 0, last: 0 }; };
  return h('table', { className: 'legend-table' }, h('thead', null, h('tr', null, h('th', null, 'Series'), h('th', null, 'Mean'), h('th', null, 'Max'), h('th', null, 'Last'))),
    h('tbody', null, series.map((s) => { const st = stats(s.values); return h('tr', { key: s.name }, h('td', null, h('i', { style: { background: s.color } }), s.name), h('td', { className: 'num' }, format(st.mean)), h('td', { className: 'num' }, format(st.max)), h('td', { className: 'num' }, format(st.last))); })));
}

function TimeSeries({ labels, series, height = 230, legend = true, yFormat, refLine, format = money }) {
  return h(Fragment, null, h(LineChart, { labels, series: series.map((s) => ({ ...s, smooth: true })), height, yFormat, refLine }), legend && h(LegendTable, { series: series.filter((s) => !s.dashed), format }));
}

/* ---------------------------------------------------------------- primitives */
function Card({ title, icon, iconTone, action, meta, children, className = '', style }) {
  return h('section', { className: 'card ' + className, style }, (title || action) && h('div', { className: 'card-head' }, icon && h(Icon, { name: icon, className: 'head-icon ' + (iconTone || '') }), title && h('h2', null, title), meta && h('span', { className: 'meta' }, meta), action), children);
}
function Delta({ value, goodWhenDown = true, suffix = 'vs last month' }) {
  if (value == null || !isFinite(value)) return h('span', null, 'No prior period');
  const down = value < 0; const good = goodWhenDown ? down : !down;
  return h(Fragment, null, h('span', { className: 'delta ' + (good ? 'good' : 'bad') }, h(Icon, { name: down ? 'down' : 'up', size: 14, stroke: 2.4 }), Math.abs(value).toFixed(1) + '%'), ' ' + suffix);
}
function Pill({ tone, children }) { return h('span', { className: 'pill ' + tone }, children); }
function Tabs({ tabs, active, onChange }) { return h('div', { className: 'tabs', role: 'tablist' }, tabs.map(([key, label]) => h('button', { key, role: 'tab', 'aria-selected': active === key, className: 'tab ' + (active === key ? 'active' : ''), onClick: () => onChange(key) }, label))); }
function Progress({ value, color }) { return h('div', { className: 'progress' }, h('div', { style: { width: Math.max(0, Math.min(100, value)) + '%', background: color } })); }
function Stat({ label, value, note }) { return h('div', { className: 'card stat' }, h('div', { className: 'label' }, label), h('div', { className: 'value num' }, value), note && h('div', { className: 'note' }, note)); }
function Table({ headers, rows, empty = 'No data available.' }) {
  if (!rows || !rows.length) return h('div', { className: 'empty' }, empty);
  return h('div', { className: 'table-scroll' }, h('table', { className: 'table' }, h('thead', null, h('tr', null, headers.map((c, i) => h('th', { key: i, className: c.right ? 'right' : '' }, c.label)))), h('tbody', null, rows.map((r, ri) => h('tr', { key: r.id || r.key || ri }, headers.map((c, ci) => h('td', { key: ci, className: (c.right ? 'right num' : '') }, c.render ? c.render(r) : r[c.key])))))));
}
function Warnings({ warnings }) {
  if (!warnings || !warnings.length) return null;
  return h('div', { className: 'banner', role: 'status' }, h(Icon, { name: 'alert', size: 18 }), h('div', null, h('strong', null, 'Partial data. '), warnings.map((w, i) => h('div', { key: i }, `${w.service}: ${w.message}`))));
}

/* ---------------------------------------------------------------- derived metrics */
function budgetStatus(util, alertAt) {
  if (util == null) return { tone: 'neutral', label: 'No budget set' };
  if (util > 100) return { tone: 'bad', label: 'Over budget' };
  if (util >= alertAt) return { tone: 'warn', label: 'Approaching limit' };
  return { tone: 'ok', label: 'On track' };
}
function healthChecks(dashboard, governance, settings) {
  const s = dashboard.summary || {}, g = governance || {}, alertAt = Number((settings.settings || {}).alert_threshold || 80);
  const util = s.budget_utilization;
  const budgetScore = util == null ? 100 : util <= alertAt ? 100 : util <= 100 ? 75 : Math.max(0, 100 - (util - 100) * 3);
  return [
    { label: 'Cost allocation (tag coverage)', score: (g.aws || {}).overall },
    { label: 'Kubernetes request policy', score: (g.kubernetes || {}).requests_compliance },
    { label: 'Kubernetes limit policy', score: (g.kubernetes || {}).limits_compliance },
    { label: 'Cloud budget control', score: budgetScore },
    { label: 'AI budget control', score: (g.ai || {}).budget_compliance },
  ].filter((c) => c.score != null).map((c) => ({ ...c, score: Math.round(c.score), tone: c.score >= 85 ? 'ok' : c.score >= 60 ? 'warn' : 'bad' }));
}
function computeAlerts({ dashboard, governance, settings, anomalies }) {
  const out = [], s = (dashboard && dashboard.summary) || {}, cfg = (settings && settings.settings) || {}, alertAt = Number(cfg.alert_threshold || 80);
  const st = budgetStatus(s.budget_utilization, alertAt);
  if (st.tone !== 'ok' && st.tone !== 'neutral') out.push({ tone: st.tone, title: `Cloud + AI spend at ${pct(s.budget_utilization)} of the ${money(s.monthly_budget)} monthly budget`, sub: `Alert threshold is ${alertAt}%. Review the forecast before month end.`, page: 'costs', tab: 'forecast' });
  const ai = (governance && governance.ai) || {};
  if (ai.budget_utilization >= alertAt) out.push({ tone: ai.budget_utilization >= 100 ? 'bad' : 'warn', title: `AI spend at ${pct(ai.budget_utilization)} of its ${money(ai.monthly_budget)} budget`, sub: `${money(ai.spend)} spent across providers this period.`, page: 'ai', tab: 'overview' });
  ((anomalies && anomalies.anomalies) || []).forEach((a) => out.push({ tone: a.severity === 'HIGH' ? 'bad' : 'warn', title: a.title, sub: `${a.primary_cause}: ${a.detail}`, page: 'ai', tab: 'anomalies' }));
  const aws = (governance && governance.aws) || {};
  const nonCompliant = (aws.resources || []).filter((r) => !r.compliant).length;
  if (nonCompliant) out.push({ tone: aws.overall < 60 ? 'bad' : 'warn', title: `${nonCompliant} AWS resources are missing required tags`, sub: `Tag coverage is ${pct(aws.overall)}. Untagged spend cannot be allocated to an owner.`, page: 'budgets', tab: 'governance' });
  const k8s = (governance && governance.kubernetes) || {};
  if ((k8s.workloads_without_requests || []).length) out.push({ tone: 'warn', title: `${k8s.workloads_without_requests.length} Kubernetes workload(s) without resource requests`, sub: k8s.workloads_without_requests.join(', '), page: 'budgets', tab: 'governance' });
  return out;
}

/* ---------------------------------------------------------------- overview */
function Overview({ data, go, onExplain }) {
  const [dashboard, forecast, governance, ai, settings, recs] = data;
  const s = dashboard.summary || {};
  const history = dashboard.history || [];
  const totals = history.map((p) => p.total), aiHist = history.map((p) => p.AI);
  const alertAt = Number((settings.settings || {}).alert_threshold || 80);
  const status = budgetStatus(s.budget_utilization, alertAt);
  const [range, setRange] = useState('forecast');
  const groups = groupByCategory(recs.recommendations || []);
  const lastPeriod = history.length ? history[history.length - 1].period : null;

  const projections = forecast.projections || [];
  const showFc = range === 'forecast';
  const labels = history.map((p) => periodLabel(p.period)).concat(showFc && lastPeriod ? projections.map((p) => periodLabel(addMonths(lastPeriod, p.month))) : []);
  const pad = (arr, n) => arr.concat(Array(n).fill(null));
  const fcStart = Array(Math.max(0, history.length - 1)).fill(null).concat(totals.length ? [totals[totals.length - 1]] : []);
  const trendSeries = [{ name: 'Total spend', values: pad(totals, showFc ? projections.length : 0), color: 'var(--green)', fill: true }];
  if (showFc) trendSeries.push({ name: 'Forecast', values: fcStart.concat(projections.map((p) => p.baseline)), color: 'var(--green)', dashed: true, width: 2 });

  const platforms = (dashboard.platforms || []).map((p) => ({ name: p.name, value: p.spend, savings: p.savings, color: PLATFORM_COLORS[p.name] || 'var(--blue)' }));
  const platformTotal = sum(platforms.map((p) => p.value));

  const topModel = (ai.models || [])[0];
  const checks = healthChecks(dashboard, governance, settings);
  const health = checks.length ? Math.round(sum(checks.map((c) => c.score)) / checks.length) : 0;
  const healthLabel = health >= 85 ? 'Excellent' : health >= 70 ? 'Good' : 'Needs attention';

  const fcLabels = history.slice(-3).map((p) => periodLabel(p.period)).concat(projections.map((p) => periodLabel(addMonths(lastPeriod, p.month))));
  const fcActual = totals.slice(-3).concat(Array(projections.length).fill(null));
  const fcBase = Array(Math.max(0, Math.min(3, totals.length) - 1)).fill(null).concat([totals[totals.length - 1]]).concat(projections.map((p) => p.baseline));
  const crossing = projections.find((p) => s.monthly_budget && p.baseline > s.monthly_budget);

  const top = groups[0];
  const insightBars = groups.slice(0, 6).reverse();
  const maxBar = Math.max(...insightBars.map((g) => g.savings), 1);
  const idle = groups.filter((g) => ['idle-instance', 'stopped-instance', 'idle-rds', 'node-consolidation', 'unattached-volume'].includes(g.category));
  const idleSavings = sum(idle.map((g) => g.savings));
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  return h(Fragment, null,
    h('div', { className: 'page-head' }, h('div', null, h('h1', null, `${greeting}, ${PROFILE.name.split(' ')[0]} 👋`), h('p', null, `Here's your cloud and AI financial overview for ${periodLabel(lastPeriod, true) || 'this period'}.`))),
    h(Warnings, { warnings: dashboard.warnings }),
    h('div', { className: 'grid kpis' },
      h('div', { className: 'card kpi' }, h('div', { className: 'kpi-icon' }, h(Icon, { name: 'wallet' })), h('div', { className: 'kpi-body' }, h('div', { className: 'kpi-label' }, 'Total Cloud + AI Spend'), h('div', { className: 'kpi-value num' }, money(s.total_monthly_spend)), h('div', { className: 'kpi-foot' }, h(Delta, { value: change(totals) }))), h(Sparkline, { values: totals.slice(-8) })),
      h('div', { className: 'card kpi' }, h('div', { className: 'kpi-icon orange' }, h(Icon, { name: 'zap' })), h('div', { className: 'kpi-body' }, h('div', { className: 'kpi-label' }, 'Optimization Opportunity'), h('div', { className: 'kpi-value num' }, money(s.potential_monthly_savings)), h('div', { className: 'kpi-foot' }, h('span', { className: 'delta bad' }, pct(s.waste_pct)), ' of spend · ', number(s.finding_count), ' findings'))),
      h('div', { className: 'card kpi' }, h('div', { className: 'kpi-icon purple' }, h(Icon, { name: 'sparkles' })), h('div', { className: 'kpi-body' }, h('div', { className: 'kpi-label' }, 'AI Inference Spend'), h('div', { className: 'kpi-value num' }, money(s.ai_spend)), h('div', { className: 'kpi-foot' }, h(Delta, { value: change(aiHist) }))), h(Sparkline, { values: aiHist.slice(-8), color: 'var(--purple)' })),
      h('div', { className: 'card budget-kpi' }, h(Ring, { value: s.budget_utilization, size: 92, color: status.tone === 'bad' ? 'var(--red)' : status.tone === 'warn' ? 'var(--amber)' : 'var(--green)', label: s.budget_utilization == null ? '—' : Math.round(s.budget_utilization) + '%' }), h('div', null, h('div', { className: 'label' }, 'Budget Utilization'), h('div', { className: 'status ' + status.tone }, status.label), h('div', { className: 'note', style: { marginTop: 8 } }, `${compact(s.total_monthly_spend)} / ${compact(s.monthly_budget)}`)))),

    h('div', { className: 'grid row-trend gap-top' },
      h(Card, { title: 'Spending Trend', icon: 'chart', action: h('div', { style: { marginLeft: 'auto' } }, h(Tabs, { tabs: [['history', '12 months'], ['forecast', '+ Forecast'], ['stacked', 'By platform']], active: range, onChange: setRange })) },
        range === 'stacked' ? h('div', { className: 'chart-legend' }, ['AWS', 'Kubernetes', 'AI'].map((p) => h('span', { key: p }, h('i', { className: 'legend-dot', style: { background: PLATFORM_COLORS[p] } }), p))) : h('div', { className: 'chart-legend' }, h('span', null, h('i', { className: 'legend-dot', style: { background: 'var(--green)' } }), 'Total spend'), showFc && h('span', { style: { color: 'var(--green)' } }, h('i', { className: 'legend-dash' }), h('span', { style: { color: 'var(--text-2)' } }, `Forecast (${forecast.method || 'scenario'})`))),
        range === 'stacked' ? h(BarChart, { labels: history.map((p) => periodLabel(p.period)), stacked: true, height: 250, series: ['AWS', 'Kubernetes', 'AI'].map((p) => ({ name: p, values: history.map((r) => r[p]), color: PLATFORM_COLORS[p] })) })
          : h(LineChart, { labels, series: trendSeries.map((x) => ({ ...x, smooth: true })), highlight: totals.length ? { index: totals.length - 1, value: totals[totals.length - 1], color: 'var(--green)' } : null })),
      h(Card, { title: 'Spend by Platform', icon: 'cloud', action: h('button', { className: 'link', onClick: () => go('costs', 'aws') }, 'View details', h(Icon, { name: 'arrowRight', size: 15 })) },
        h('div', { className: 'donut-wrap' }, h(Donut, { items: platforms, size: 138, stroke: 24, centerLabel: compact(platformTotal), centerSub: 'Total spend' }),
          h('div', { className: 'legend-list' }, platforms.map((p) => h('div', { className: 'legend-row', key: p.name }, h('span', { className: 'name' }, h('i', { className: 'legend-dot', style: { background: p.color } }), p.name), h('span', { className: 'muted num' }, pct(p.value / (platformTotal || 1) * 100)), h('span', { className: 'num' }, money(p.value)))))))),

    h('div', { className: 'grid row-three gap-top' },
      h(Card, { title: 'Top Optimization Opportunities', icon: 'zap', iconTone: 'orange', action: h('button', { className: 'link', onClick: () => go('optimization', 'all') }, 'View all', h(Icon, { name: 'arrowRight', size: 15 })) },
        h(Table, { headers: [
          { label: 'Opportunity', render: (g) => h('div', { className: 'opp-name' }, h('span', { className: 'opp-icon' }, h(Icon, { name: catIcon(g.category), size: 16 })), h('span', null, catLabel(g.category), ' ', h('span', { className: 'count' }, `(${g.count})`))) },
          { label: 'Savings / mo', render: (g) => h('span', { className: 'num nowrap' }, money(g.savings)) },
          { label: 'Effort', render: (g) => h(Pill, { tone: effortOf(g.effort) }, g.effort) },
          { label: 'Action', render: (g) => h('button', { className: 'btn', onClick: () => go('optimization', 'all', g.category) }, 'Review') },
        ], rows: groups.slice(0, 5).map((g) => ({ ...g, key: g.category })), empty: 'No savings opportunities at the current thresholds.' })),
      h(Card, { title: 'AI FinOps Insights', icon: 'sparkles', className: '', style: { position: 'relative' } },
        h('div', { className: 'potential' }, h('strong', { className: 'num' }, compact(s.potential_monthly_savings)), h('span', null, 'Potential')),
        top ? h('div', { className: 'insight' },
          h('div', null, h('div', { className: 'insight-copy' }, 'You can save up to', h('strong', { className: 'num' }, money(s.potential_monthly_savings) + ' a month'), `Biggest lever: ${catLabel(top.category).toLowerCase()}, worth ${money(top.savings)} across ${top.count} finding${top.count > 1 ? 's' : ''}.`), h('button', { className: 'btn lg', style: { marginTop: 18 }, onClick: () => go('optimization', 'all', top.category) }, 'View details', h(Icon, { name: 'arrowRight', size: 15 }))),
          h('div', { className: 'bars', 'aria-label': 'Savings by category' }, insightBars.map((g, i) => h('div', { key: g.category, className: 'bar ' + (i === insightBars.length - 1 ? 'top' : ''), title: `${catLabel(g.category)}: ${money(g.savings)}`, style: { height: Math.max(6, g.savings / maxBar * 100) + '%' } }))))
          : h('div', { className: 'empty' }, 'No insights yet.')),
      h(Card, { title: 'AI Workload Economics', icon: 'cpu', action: h('span', { className: 'live' }, dashboard.mode === 'live' ? 'Live' : 'Demo data') },
        h('div', { className: 'big-value num' }, compact(ai.monthly_spend), h('small', null, ' / month')),
        h('div', { className: 'kpi-foot', style: { marginTop: 4 } }, 'AI token costs · ', h(Delta, { value: change(aiHist), suffix: 'MoM' })),
        h(AreaSpark, { values: aiHist }),
        h('div', { className: 'econ-foot' }, 'Top model', h('strong', null, topModel ? topModel.model : '—'), h('span', { className: 'right num' }, topModel ? `${compact(topModel.cost)} (${pct(topModel.cost / (ai.monthly_spend || 1) * 100, 0)})` : '')),
        h('div', { className: 'econ-foot' }, 'Blended cost / 1K tokens', h('span', { className: 'right num' }, '$' + Number(ai.cost_per_1k_tokens || 0).toFixed(4))))),

    h('div', { className: 'grid row-bottom gap-top' },
      h(Card, { title: 'FinOps Health Score', icon: 'heart', iconTone: 'orange' },
        h('div', { className: 'health' }, h('div', null, h(Ring, { value: health, size: 118, stroke: 12, label: String(health) }), h('div', { className: 'ring-label' }, healthLabel)),
          h('div', null, checks.map((c) => h('div', { className: 'check', key: c.label }, h('span', { className: 'check-icon ' + c.tone }, h(Icon, { name: c.tone === 'ok' ? 'check' : 'alert', size: 11, stroke: 3 })), c.label, h('span', { className: 'score num' }, c.score + '%'))), h('div', { className: 'note', style: { marginTop: 6 } }, 'Average of the governance controls above.')))),
      h(Card, { title: 'Forecast vs Budget', icon: 'chart', meta: crossing ? h(Pill, { tone: 'bad' }, `Exceeds budget in ${periodLabel(addMonths(lastPeriod, crossing.month))}`) : h(Pill, { tone: 'ok' }, 'Within budget') },
        h(LineChart, { labels: fcLabels, height: 200, series: [{ name: 'Actual', values: fcActual, color: 'var(--green)', fill: true }, { name: 'Forecast', values: fcBase, color: 'var(--green)', dashed: true, width: 2 }], refLine: s.monthly_budget ? { value: s.monthly_budget, color: 'var(--orange)', label: 'Budget ' + compact(s.monthly_budget) } : null })),
      h('section', { className: 'card green-card' },
        h('div', { className: 'copy' }, h('h3', null, 'Idle capacity costs twice'), h('p', null, `${money(idleSavings)} a month of idle or orphaned resources identified. Removing them cuts spend and emissions together. Carbon is not measured yet.`), h('button', { className: 'btn', onClick: () => go('costs', 'waste') }, 'Review idle resources', h(Icon, { name: 'arrowRight', size: 14 }))),
        h(Scene))));
}

function Scene() {
  const turbine = (x, y, s, rot) => h('g', { transform: `translate(${x} ${y}) scale(${s})` }, h('path', { d: 'M-1.5 0 L-3 70 L3 70 L1.5 0Z', fill: '#f4f7f5' }), h('g', { transform: `rotate(${rot})` }, [0, 120, 240].map((a) => h('path', { key: a, d: 'M0 0 L-2.5 -34 Q0 -38 2.5 -34Z', fill: '#ffffff', transform: `rotate(${a})` }))), h('circle', { r: 2.6, fill: '#dfe7e2' }));
  return h('svg', { className: 'scene', viewBox: '0 0 400 200', preserveAspectRatio: 'xMaxYMax slice', 'aria-hidden': 'true' },
    h('path', { d: 'M0 150 Q80 110 170 140 T400 120 V200 H0Z', fill: '#9cc9ad', opacity: .55 }),
    h('path', { d: 'M0 175 Q110 140 230 165 T400 150 V200 H0Z', fill: '#4f9a72', opacity: .75 }),
    h('path', { d: 'M0 192 Q140 170 260 188 T400 182 V200 H0Z', fill: '#1f6b46' }),
    turbine(300, 70, 1, 12), turbine(352, 92, .75, 47), turbine(250, 104, .55, 80),
    [40, 62, 84, 130, 160].map((x, i) => h('path', { key: i, d: `M${x} 190 l7 -22 l7 22z`, fill: '#145236', opacity: .9 })));
}

/* ---------------------------------------------------------------- metrics (Grafana-style dashboard) */
function clusterUtil(nodes) {
  const cap = (k) => sum((nodes || []).map((n) => n[k]));
  return { cpu: cap('cpu_capacity') ? cap('cpu_usage') / cap('cpu_capacity') * 100 : 0, mem: cap('memory_capacity') ? cap('memory_usage') / cap('memory_capacity') * 100 : 0, cpuReq: cap('cpu_capacity') ? cap('cpu_requested') / cap('cpu_capacity') * 100 : 0, memReq: cap('memory_capacity') ? cap('memory_requested') / cap('memory_capacity') * 100 : 0 };
}
function cacheHitRate(usage) {
  const input = sum((usage || []).map((u) => u.input_tokens));
  return input ? sum((usage || []).map((u) => u.input_tokens * (u.cache_hit_rate || 0))) / input * 100 : 0;
}
const UTIL_BAND = T.band(20, 40, 80);

function MetricsPage({ tab, data }) {
  const [dashboard, k8s, ai, governance, settings, waste] = data;
  const months = Number(tab || 12);
  const s = dashboard.summary || {}, cfg = settings.settings || {}, alertAt = Number(cfg.alert_threshold || 80);
  const history = (dashboard.history || []).slice(-months);
  const labels = history.map((p) => periodLabel(p.period));
  const platformSeries = ['AWS', 'Kubernetes', 'AI'].map((p) => ({ name: p, values: history.map((r) => r[p]), color: PLATFORM_COLORS[p] }));
  const totals = history.map((p) => p.total);
  const nodes = k8s.nodes || [], util = clusterUtil(nodes);
  const usage = ai.usage || [], models = ai.models || [];
  const wasteItems = Object.entries(waste.by_category || {}).map(([k, v]) => { const [platform, cat] = k.split(' · '); return { label: catLabel(cat || k), value: v, color: PLATFORM_COLORS[platform] }; });
  const tagCoverage = (governance.aws || {}).overall || 0;
  const delta = change(totals);
  return h('div', { className: 'gf-grid' },
    h('div', { className: 'gf-row' }, h(Icon, { name: 'wallet', size: 15 }), 'Spend'),
    h(Panel, { span: 3, title: 'Total spend', info: 'AWS + Kubernetes + AI for the latest month. Sparkline shows the selected range.' }, h(StatPanel, { value: s.total_monthly_spend, display: money(s.total_monthly_spend), spark: totals, color: 'var(--green)', sub: delta == null ? '' : `${delta >= 0 ? '▲' : '▼'} ${Math.abs(delta).toFixed(1)}% vs last month` })),
    h(Panel, { span: 3, title: 'Potential savings', info: 'Unique, deduplicated opportunities. Colour follows waste as a share of spend.' }, h(StatPanel, { value: s.waste_pct, display: money(s.potential_monthly_savings), thresholds: T.lowerIsBetter(5, 10), sub: `${number(s.finding_count)} findings · ${pct(s.waste_pct)} of spend` })),
    h(Panel, { span: 3, title: 'Budget used', info: `Thresholds: amber at the ${alertAt}% alert line, red above 100%.` }, h(Gauge, { value: s.budget_utilization || 0, max: 120, thresholds: T.lowerIsBetter(alertAt, 100), label: `${compact(s.total_monthly_spend)} of ${compact(s.monthly_budget)}` })),
    h(Panel, { span: 3, title: 'Waste ratio', info: 'Potential savings / total spend. Under 5% is healthy.' }, h(Gauge, { value: s.waste_pct || 0, max: 20, decimals: 1, thresholds: T.lowerIsBetter(5, 10), label: 'of monthly spend' })),
    h(Panel, { span: 7, title: 'Spend by platform', info: 'Monthly cost per platform with mean, max and last values.', right: `${months} months` }, h(TimeSeries, { labels, series: platformSeries, height: 220 })),
    h(Panel, { span: 5, title: 'Monthly spend composition', info: 'Stacked monthly spend. Hover a bar for the split.' }, h(BarChart, { labels, series: platformSeries, stacked: true, height: 262 })),

    h('div', { className: 'gf-row' }, h(Icon, { name: 'cube', size: 15 }), 'Efficiency'),
    h(Panel, { span: 3, title: 'Tag coverage', info: 'Share of AWS resources carrying every required tag.' }, h(Gauge, { value: tagCoverage, thresholds: T.higherIsBetter(60, 85), decimals: 1, label: 'required tags present' })),
    h(Panel, { span: 3, title: 'Cluster CPU utilization', info: 'Actual CPU usage / node capacity. Under 40% is paid-for idle capacity; over 80% is saturation risk.' }, h(Gauge, { value: util.cpu, thresholds: UTIL_BAND, decimals: 1, label: `requested ${pct(util.cpuReq, 0)}` })),
    h(Panel, { span: 3, title: 'Cluster memory utilization', info: 'Actual memory usage / node capacity.' }, h(Gauge, { value: util.mem, thresholds: UTIL_BAND, decimals: 1, label: `requested ${pct(util.memReq, 0)}` })),
    h(Panel, { span: 3, title: 'AI cache hit rate', info: 'Input-token-weighted share of prompt tokens served from cache.' }, h(Gauge, { value: cacheHitRate(usage), max: 60, thresholds: T.higherIsBetter(10, 25), decimals: 1, label: 'of input tokens' })),
    h(Panel, { span: 6, title: 'Node CPU utilization', info: 'Per node, LCD bar gauge coloured by the utilization band.' }, h(BarGauge, { items: nodes.map((n) => ({ label: n.name, sub: n.instance_type, value: n.cpu_utilization * 100 })), max: 100, thresholds: UTIL_BAND })),
    h(Panel, { span: 6, title: 'Node memory utilization', info: 'Per node, LCD bar gauge coloured by the utilization band.' }, h(BarGauge, { items: nodes.map((n) => ({ label: n.name, sub: n.instance_type, value: n.memory_utilization * 100 })), max: 100, thresholds: UTIL_BAND })),
    h(Panel, { span: 6, title: 'Workload efficiency', info: 'Average of CPU and memory usage / requests. Low efficiency means over-requested capacity.' }, h(BarGauge, { mode: 'gradient', items: (k8s.workloads || []).map((w) => ({ label: w.name, sub: w.namespace, value: w.efficiency * 100 })).sort((a, b) => a.value - b.value), max: 100, thresholds: T.higherIsBetter(40, 60) })),
    h(Panel, { span: 6, title: 'Namespace cost share', info: 'Share of allocated cluster cost per namespace.' }, h(BarGauge, { mode: 'gradient', items: (k8s.namespaces || []).map((n) => ({ label: n.namespace, sub: money(n.monthly_cost), value: n.cluster_cost_pct })), max: 100, thresholds: [{ value: -Infinity, color: 'var(--teal)' }, { value: 50, color: 'var(--blue)' }] })),

    h('div', { className: 'gf-row' }, h(Icon, { name: 'sparkles', size: 15 }), 'Optimization & AI'),
    h(Panel, { span: 6, title: 'Savings by category', info: 'Monthly savings estimate, coloured by platform.' }, h(HBarChart, { items: wasteItems })),
    h(Panel, { span: 6, title: 'Tokens by model', info: 'Input vs output tokens for the latest period.' }, h(BarChart, { labels: models.map((m) => m.model), series: [{ name: 'Input tokens', values: models.map((m) => m.input_tokens), color: '#2a9d8f' }, { name: 'Output tokens', values: models.map((m) => m.output_tokens), color: '#7c5cd6' }], yFormat: tokens, valueFormat: tokens, height: 240 })),
    h(Panel, { span: 6, title: 'Cost per 1K tokens', info: 'Blended unit price per model. Lower is cheaper per unit of work.' }, h(HBarChart, { items: models.map((m) => ({ label: m.model, value: m.cost_per_1k_tokens })).sort((a, b) => b.value - a.value), format: (v) => '$' + Number(v).toFixed(4), color: 'var(--purple)' })),
    h(Panel, { span: 6, title: 'AI spend by application', info: 'Monthly AI cost allocated to the application creating the demand.' }, h(HBarChart, { items: (ai.applications || []).map((a) => ({ label: a.application, value: a.cost })), color: 'var(--green)' })));
}

/* ---------------------------------------------------------------- recommendation table */
function RecommendationTable({ items, onExplain }) {
  return h(Table, { empty: 'No findings match the current filters and thresholds.', headers: [
    { label: 'Finding', render: (f) => h('div', { className: 'opp-name' }, h('span', { className: 'opp-icon' }, h(Icon, { name: catIcon(f.category), size: 16 })), h('div', null, h('div', { className: 'cell-title' }, f.issue), h('div', { className: 'cell-sub' }, f.recommendation))) },
    { label: 'Platform', render: (f) => h('span', { className: 'platform-badge ' + ({ AWS: 'aws', Kubernetes: 'k8s', AI: 'ai' }[f.platform] || '') }, f.platform) },
    { label: 'Savings / mo', right: true, render: (f) => money2(f.estimated_monthly_savings) },
    { label: 'Confidence', render: (f) => h(Pill, { tone: { High: 'low', Medium: 'medium', Low: 'high' }[f.confidence] || 'neutral' }, f.confidence) },
    { label: 'Risk', render: (f) => h(Pill, { tone: effortOf(f.risk) }, f.risk) },
    { label: '', render: (f) => h('button', { className: 'btn ghost', onClick: () => onExplain(f) }, 'Explain') },
  ], rows: items });
}

/* ---------------------------------------------------------------- pages */
function CostsPage({ tab, data, onExplain }) {
  const [d, histResp] = data;
  if (tab === 'aws') {
    const entries = (obj) => Object.entries(obj || {}).map(([name, value]) => ({ name, value, share: value / (d.total_monthly_cost || 1) * 100, key: name })).sort((a, b) => b.value - a.value);
    const svc = entries(d.by_service);
    return h(Fragment, null,
      h('div', { className: 'metric-strip' }, h(Stat, { label: 'Monthly AWS spend', value: money(d.total_monthly_cost), note: 'Cost Explorer (demo dataset in demo mode)' }), h(Stat, { label: 'Services', value: number(svc.length) }), h(Stat, { label: 'Regions', value: number(Object.keys(d.by_region || {}).length) }), h(Stat, { label: 'Teams allocated', value: number(Object.keys(d.by_team || {}).length), note: 'From cost allocation tags' })),
      h('div', { className: 'gf-grid', style: { marginBottom: 18 } },
        h(Panel, { span: 7, title: 'Monthly spend by platform', info: 'Stacked AWS, Kubernetes and AI cost per month.' }, h(BarChart, { labels: ((histResp && histResp.history) || []).map((p) => periodLabel(p.period)), stacked: true, height: 250, series: ['AWS', 'Kubernetes', 'AI'].map((p) => ({ name: p, values: ((histResp && histResp.history) || []).map((r) => r[p]), color: PLATFORM_COLORS[p] })) })),
        h(Panel, { span: 5, title: 'Top services', info: 'Monthly AWS cost by service.' }, h(HBarChart, { items: svc.map((r, i) => ({ label: r.name, value: r.value, color: SERIES_COLORS[i % SERIES_COLORS.length] })) }))),
      h('div', { className: 'grid two' },
        h(Card, { title: 'Spend by service', icon: 'chart' }, h(Table, { headers: [{ label: 'Service', key: 'name' }, { label: 'Share', render: (r) => h('div', { style: { minWidth: 110 } }, h(Progress, { value: r.share, color: 'var(--green)' })) }, { label: 'Cost', right: true, render: (r) => money(r.value) }, { label: '%', right: true, render: (r) => pct(r.share) }], rows: svc })),
        h(Card, { title: 'Allocation views', icon: 'layers' }, h(Table, { headers: [{ label: 'Dimension', key: 'name' }, { label: 'Cost', right: true, render: (r) => money(r.value) }, { label: '%', right: true, render: (r) => pct(r.share) }], rows: entries(d.by_team).map((r) => ({ ...r, name: 'Team · ' + r.name, key: 't' + r.name })).concat(entries(d.by_environment).map((r) => ({ ...r, name: 'Environment · ' + r.name, key: 'e' + r.name }))).concat(entries(d.by_region).map((r) => ({ ...r, name: 'Region · ' + r.name, key: 'r' + r.name }))) }))));
  }
  if (tab === 'waste') {
    const cats = Object.entries(d.by_category || {}).map(([k, v]) => ({ key: k, name: k, value: v }));
    const max = Math.max(...cats.map((c) => c.value), 1);
    return h(Fragment, null,
      h('div', { className: 'metric-strip' }, h(Stat, { label: 'Identified waste', value: money(d.total_waste), note: 'Monthly, unique findings' }), h(Stat, { label: 'Findings', value: number((d.findings || []).length) }), h(Stat, { label: 'High priority', value: number((d.findings || []).filter((f) => f.priority === 'HIGH').length) }), h(Stat, { label: 'Remediation', value: 'Manual', note: 'Nothing is auto-applied' })),
      h('div', { className: 'grid two' }, h(Card, { title: 'Waste by category', icon: 'chart' }, h(HBarChart, { items: cats.map((c) => { const [platform, cat] = c.name.split(' · '); return { label: catLabel(cat || c.name), value: c.value, color: PLATFORM_COLORS[platform] }; }) })),
        h(Card, { title: 'How savings are counted', icon: 'shield' }, h('div', { className: 'callout' }, h('strong', null, 'One identity per opportunity. '), 'Each finding is keyed by platform + resource + category, so the same dollars cannot be counted twice across the waste, optimization, and platform views. Every number is an estimate with a confidence and risk rating, and should be validated before action.'))),
      h(Card, { title: 'Waste findings', icon: 'zap', iconTone: 'orange', className: 'gap-top' }, h(RecommendationTable, { items: d.findings || [], onExplain })));
  }
  const history = d.historical || [], proj = d.projections || [], last = history.length ? history[history.length - 1].period : null;
  const labels = history.map((p) => periodLabel(p.period)).concat(proj.map((p) => periodLabel(addMonths(last, p.month))));
  const actual = history.map((p) => p.total).concat(Array(proj.length).fill(null));
  const join = Array(Math.max(0, history.length - 1)).fill(null).concat(history.length ? [history[history.length - 1].total] : []);
  return h(Fragment, null,
    h('div', { className: 'metric-strip' }, h(Stat, { label: 'Method', value: d.method || '—', note: 'Explicit, explainable assumptions' }), h(Stat, { label: 'Growth assumption', value: pct((d.growth_rate || 0) * 100), note: 'Monthly, set in Settings' }), h(Stat, { label: 'Horizon', value: number(d.horizon_months) + ' months' }), h(Stat, { label: 'Next month (baseline)', value: money(proj[0] && proj[0].baseline) })),
    h(Card, { title: 'Spend history and scenarios', icon: 'trend' }, h('div', { className: 'chart-legend' }, h('span', null, h('i', { className: 'legend-dot', style: { background: 'var(--green)' } }), 'Actual'), h('span', null, h('i', { className: 'legend-dot', style: { background: 'var(--orange)' } }), 'Baseline'), h('span', null, h('i', { className: 'legend-dot', style: { background: 'var(--teal)' } }), 'Optimized scenarios')),
      h(LineChart, { labels, height: 260, series: [{ name: 'Actual', values: actual, color: 'var(--green)', fill: true }, { name: 'Baseline', values: join.concat(proj.map((p) => p.baseline)), color: 'var(--orange)', dashed: true }, { name: 'Conservative optimization', values: join.concat(proj.map((p) => p.conservative)), color: 'var(--teal)', dashed: true, width: 1.8 }, { name: 'Aggressive optimization', values: join.concat(proj.map((p) => p.aggressive)), color: 'var(--green-mid)', dashed: true, width: 1.6 }] })),
    h(Card, { title: 'Scenario table', icon: 'calendar', className: 'gap-top' }, h(Table, { headers: [{ label: 'Month', render: (r) => periodLabel(addMonths(last, r.month), true) }, { label: 'Baseline', right: true, render: (r) => money(r.baseline) }, { label: 'Conservative optimization', right: true, render: (r) => money(r.conservative) }, { label: 'Aggressive optimization', right: true, render: (r) => money(r.aggressive) }], rows: proj.map((p) => ({ ...p, key: p.month })) })));
}

function OptimizationPage({ tab, data, filter, query, onExplain, go }) {
  const [d] = data;
  let items = d.recommendations || [];
  if (tab !== 'all') items = items.filter((f) => f.platform.toLowerCase() === tab);
  if (filter) items = items.filter((f) => f.category === filter);
  if (query) { const q = query.toLowerCase(); items = items.filter((f) => [f.issue, f.recommendation, f.resource_id, f.category, f.platform, f.service].join(' ').toLowerCase().includes(q)); }
  const savings = sum(items.map((f) => f.estimated_monthly_savings));
  return h(Fragment, null,
    h('div', { className: 'metric-strip' }, h(Stat, { label: 'Savings in view', value: money(savings), note: 'Monthly estimate' }), h(Stat, { label: 'Findings', value: number(items.length) }), h(Stat, { label: 'High priority', value: number(items.filter((f) => f.priority === 'HIGH').length) }), h(Stat, { label: 'Queue total', value: money(d.total_potential_savings), note: 'All platforms, deduplicated' })),
    (filter || query) && h('div', { className: 'banner', style: { background: 'var(--green-soft)', borderColor: 'transparent' } }, h(Icon, { name: 'search', size: 16 }), h('div', null, 'Filtered by ', filter && h('strong', null, catLabel(filter) + ' '), query && h('strong', null, `"${query}" `), h('button', { className: 'link', style: { marginLeft: 8, display: 'inline' }, onClick: () => go('optimization', tab) }, 'Clear'))),
    h(Card, { title: 'Optimization queue', icon: 'zap', iconTone: 'orange', meta: 'Sorted by estimated savings' }, h(RecommendationTable, { items, onExplain })));
}

function KubernetesPage({ tab, data, onExplain }) {
  const [d] = data;
  if (tab === 'overview') {
    const c = d.cluster || {};
    return h(Fragment, null,
      h('div', { className: 'metric-strip' }, h(Stat, { label: 'Cluster cost', value: money(c.monthly_cost), note: c.name }), h(Stat, { label: 'Allocated', value: money(c.allocated_cost), note: 'To namespaces and workloads' }), h(Stat, { label: 'Unallocated', value: money(c.unallocated_cost), note: 'Visible, not counted as savings' }), h(Stat, { label: 'Allocation efficiency', value: pct(c.efficiency) })),
      h('div', { className: 'grid two' },
        h(Card, { title: 'Node utilization', icon: 'server', meta: 'CPU · memory' }, h(BarGauge, { items: (d.nodes || []).flatMap((n) => [{ key: n.node_id + 'c', label: n.name + ' · CPU', sub: n.instance_type + ' · ' + money(n.monthly_cost), value: n.cpu_utilization * 100 }, { key: n.node_id + 'm', label: n.name + ' · Mem', value: n.memory_utilization * 100 }]), max: 100, thresholds: UTIL_BAND, cells: 24 })),
        h(Card, { title: 'Namespace allocation', icon: 'layers' }, h(Table, { headers: [{ label: 'Namespace', key: 'namespace' }, { label: 'Cost', right: true, render: (r) => money(r.monthly_cost) }, { label: 'Share', right: true, render: (r) => pct(r.cluster_cost_pct) }], rows: (d.namespaces || []).map((n) => ({ ...n, key: n.namespace })) }))),
      h(Card, { title: 'Top Kubernetes opportunities', icon: 'zap', iconTone: 'orange', className: 'gap-top' }, h(RecommendationTable, { items: (d.recommendations || []).filter((f) => f.estimated_monthly_savings > 0).slice(0, 6), onExplain })));
  }
  if (tab === 'workloads') return h(Fragment, null, h('div', { className: 'gf-grid', style: { marginBottom: 18 } }, h(Panel, { span: 6, title: 'CPU efficiency', info: 'Usage / request per workload' }, h(BarGauge, { mode: 'gradient', items: (d.workloads || []).map((w) => ({ label: w.name, sub: w.namespace, value: w.cpu_efficiency * 100 })), max: 100, thresholds: T.higherIsBetter(40, 60) })), h(Panel, { span: 6, title: 'Memory efficiency', info: 'Usage / request per workload' }, h(BarGauge, { mode: 'gradient', items: (d.workloads || []).map((w) => ({ label: w.name, sub: w.namespace, value: w.memory_efficiency * 100 })), max: 100, thresholds: T.higherIsBetter(50, 70) }))), h(Card, { title: 'Requests vs actual usage', icon: 'cube', meta: 'CPU cores / memory GiB' }, h(Table, { headers: [{ label: 'Workload', render: (r) => h('div', null, h('div', { className: 'cell-title' }, r.name), h('div', { className: 'cell-sub' }, `${r.namespace} · ${r.type} · ${r.replicas} replicas`)) }, { label: 'CPU req / used', right: true, render: (r) => `${r.cpu_request} / ${r.cpu_usage}` }, { label: 'Memory req / used', right: true, render: (r) => `${r.memory_request} / ${r.memory_usage}` }, { label: 'Efficiency', render: (r) => h('div', { style: { minWidth: 100 } }, h(Progress, { value: r.efficiency * 100, color: r.efficiency < .4 ? 'var(--orange)' : 'var(--green)' })) }, { label: 'Suggested CPU / mem', right: true, render: (r) => `${r.recommended_cpu_request} / ${r.recommended_memory_request}` }, { label: 'Savings', right: true, render: (r) => money(r.estimated_savings) }], rows: (d.workloads || []).map((w) => ({ ...w, key: w.workload_id })) })));
  if (tab === 'namespaces') return h(Card, { title: 'Namespace showback', icon: 'layers' }, h(Table, { headers: [{ label: 'Namespace', key: 'namespace' }, { label: 'Workloads', right: true, key: 'workload_count' }, { label: 'Pods', right: true, key: 'pod_count' }, { label: 'CPU cost', right: true, render: (r) => money(r.cpu_cost) }, { label: 'Memory cost', right: true, render: (r) => money(r.memory_cost) }, { label: 'Total', right: true, render: (r) => money(r.monthly_cost) }, { label: 'Share', right: true, render: (r) => pct(r.cluster_cost_pct) }], rows: (d.namespaces || []).map((n) => ({ ...n, key: n.namespace })) }));
  const u = clusterUtil(d.nodes || []);
  return h(Fragment, null, h('div', { className: 'gf-grid', style: { marginBottom: 18 } },
    h(Panel, { span: 3, title: 'CPU used', info: 'Usage / capacity' }, h(Gauge, { value: u.cpu, thresholds: UTIL_BAND, decimals: 1, label: 'of capacity' })),
    h(Panel, { span: 3, title: 'CPU requested', info: 'Requests / capacity' }, h(Gauge, { value: u.cpuReq, thresholds: T.band(30, 50, 90), decimals: 1, label: 'of capacity' })),
    h(Panel, { span: 3, title: 'Memory used', info: 'Usage / capacity' }, h(Gauge, { value: u.mem, thresholds: UTIL_BAND, decimals: 1, label: 'of capacity' })),
    h(Panel, { span: 3, title: 'Memory requested', info: 'Requests / capacity' }, h(Gauge, { value: u.memReq, thresholds: T.band(30, 50, 90), decimals: 1, label: 'of capacity' })),
    h(Panel, { span: 12, title: 'Average utilization per node', info: 'Mean of CPU and memory utilization' }, h(BarGauge, { items: (d.nodes || []).map((n) => ({ label: n.name, sub: n.instance_type, value: n.utilization * 100 })), max: 100, thresholds: UTIL_BAND, cells: 40 }))),
  h(Card, { title: 'Node capacity posture', icon: 'server', meta: 'Low utilization is not proof a node can be removed' }, h(Table, { headers: [{ label: 'Node', key: 'name' }, { label: 'Instance type', key: 'instance_type' }, { label: 'CPU', right: true, render: (r) => pct(r.cpu_utilization * 100) }, { label: 'Memory', right: true, render: (r) => pct(r.memory_utilization * 100) }, { label: 'Monthly cost', right: true, render: (r) => money(r.monthly_cost) }, { label: 'Status', render: (r) => r.utilization < .3 ? h(Pill, { tone: 'medium' }, 'Underutilized') : h(Pill, { tone: 'low' }, 'Healthy') }], rows: (d.nodes || []).map((n) => ({ ...n, key: n.node_id })) })));
}

function AIPage({ tab, data, onExplain }) {
  const [d, hist] = data;
  if (tab === 'overview') {
    const history = (hist && hist.history) || [];
    return h(Fragment, null,
      h('div', { className: 'metric-strip' }, h(Stat, { label: 'Monthly AI spend', value: money(d.monthly_spend), note: 'Normalized provider usage' }), h(Stat, { label: 'Total tokens', value: tokens(d.total_tokens), note: `${tokens(d.input_tokens)} in / ${tokens(d.output_tokens)} out` }), h(Stat, { label: 'Cost / 1K tokens', value: '$' + Number(d.cost_per_1k_tokens || 0).toFixed(4), note: 'Blended across models' }), h(Stat, { label: 'Potential savings', value: money(d.potential_savings), note: 'Quality must be validated' })),
      h('div', { className: 'grid row-trend' },
        h(Card, { title: 'AI spend trend', icon: 'trend' }, h(LineChart, { labels: history.map((p) => periodLabel(p.period)), series: [{ name: 'AI spend', values: history.map((p) => p.AI), color: 'var(--purple)', fill: true }] })),
        h(Card, { title: 'Spend by model', icon: 'cpu' }, h('div', { className: 'donut-wrap' }, h(Donut, { size: 150, stroke: 26, items: (d.models || []).map((m, i) => ({ value: m.cost, color: ['#1f7a4d', '#f2711c', '#f2b632', '#7c5cd6', '#2a9d8f', '#3b6fd8'][i % 6] })), centerLabel: compact(d.monthly_spend), centerSub: 'AI spend' }), h('div', { className: 'legend-list' }, (d.models || []).map((m, i) => h('div', { className: 'legend-row', key: m.model }, h('span', { className: 'name' }, h('i', { className: 'legend-dot', style: { background: ['#1f7a4d', '#f2711c', '#f2b632', '#7c5cd6', '#2a9d8f', '#3b6fd8'][i % 6] } }), m.model), h('span', { className: 'muted num' }, pct(m.cost / (d.monthly_spend || 1) * 100, 0)), h('span', { className: 'num' }, compact(m.cost)))))))),
      h(Card, { title: 'AI optimization opportunities', icon: 'sparkles', className: 'gap-top' }, h(RecommendationTable, { items: (d.recommendations || []).filter((f) => f.estimated_monthly_savings > 0), onExplain })));
  }
  if (tab === 'usage') return h(Card, { title: 'Normalized token usage', icon: 'sparkles', meta: 'Provider-neutral records' }, h(Table, { headers: [{ label: 'Application', render: (r) => h('div', null, h('div', { className: 'cell-title' }, r.application), h('div', { className: 'cell-sub' }, `${r.team} · ${r.environment}`)) }, { label: 'Provider / model', render: (r) => h('div', null, h('div', null, r.model), h('div', { className: 'cell-sub' }, r.provider)) }, { label: 'Requests', right: true, render: (r) => number(r.request_count) }, { label: 'Input', right: true, render: (r) => tokens(r.input_tokens) }, { label: 'Output', right: true, render: (r) => tokens(r.output_tokens) }, { label: 'Cache hit', right: true, render: (r) => pct((r.cache_hit_rate || 0) * 100) }, { label: 'Latency', right: true, render: (r) => Math.round(r.latency_ms) + ' ms' }, { label: 'Cost', right: true, render: (r) => money(r.cost) }], rows: (d.usage || []).map((u, i) => ({ ...u, key: i })) }));
  if (tab === 'models') return h(Fragment, null, h('div', { className: 'gf-grid', style: { marginBottom: 18 } },
    h(Panel, { span: 7, title: 'Tokens by model', info: 'Input vs output tokens' }, h(BarChart, { labels: (d.models || []).map((m) => m.model), series: [{ name: 'Input tokens', values: (d.models || []).map((m) => m.input_tokens), color: '#2a9d8f' }, { name: 'Output tokens', values: (d.models || []).map((m) => m.output_tokens), color: '#7c5cd6' }], yFormat: tokens, valueFormat: tokens })),
    h(Panel, { span: 5, title: 'Cost per 1K tokens', info: 'Blended unit price' }, h(HBarChart, { items: (d.models || []).map((m) => ({ label: m.model, value: m.cost_per_1k_tokens })).sort((a, b) => b.value - a.value), format: (v) => '$' + Number(v).toFixed(4), color: 'var(--purple)' }))),
  h(Card, { title: 'Model economics', icon: 'cpu' }, h(Table, { headers: [{ label: 'Model', render: (r) => h('div', null, h('div', { className: 'cell-title' }, r.model), h('div', { className: 'cell-sub' }, r.provider)) }, { label: 'Requests', right: true, render: (r) => number(r.requests) }, { label: 'Tokens', right: true, render: (r) => tokens(r.total_tokens) }, { label: 'Cost / request', right: true, render: (r) => '$' + Number(r.cost_per_request).toFixed(4) }, { label: 'Cost / 1K tokens', right: true, render: (r) => '$' + Number(r.cost_per_1k_tokens).toFixed(4) }, { label: 'Latency', right: true, render: (r) => Math.round(r.latency_ms) + ' ms' }, { label: 'Cost', right: true, render: (r) => money(r.cost) }], rows: (d.models || []).map((m) => ({ ...m, key: m.model })) })));
  if (tab === 'applications') return h(Card, { title: 'Cost by application', icon: 'layers', meta: 'Showback to teams' }, h(Table, { headers: [{ label: 'Application', key: 'application' }, { label: 'Team', key: 'team' }, { label: 'Environment', key: 'environment' }, { label: 'Requests', right: true, render: (r) => number(r.requests) }, { label: 'Tokens', right: true, render: (r) => tokens(r.tokens) }, { label: 'Cost / request', right: true, render: (r) => '$' + Number(r.cost_per_request).toFixed(4) }, { label: 'Cost', right: true, render: (r) => money(r.cost) }], rows: (d.applications || []).map((a) => ({ ...a, key: a.application })) }));
  if (tab === 'anomalies') return h(Fragment, null, h('div', { className: 'metric-strip' }, h(Stat, { label: 'Open anomalies', value: number((d.anomalies || []).length) }), h(Stat, { label: 'Baseline spend', value: money(d.baseline_spend) }), h(Stat, { label: 'Current spend', value: money(d.current_spend) }), h(Stat, { label: 'Change', value: pct((d.current_spend - d.baseline_spend) / (d.baseline_spend || 1) * 100) })),
    h(Card, { title: 'Anomaly queue', icon: 'bell', meta: 'Investigate before acting' }, h(Table, { headers: [{ label: 'Severity', render: (r) => h(Pill, { tone: r.severity === 'HIGH' ? 'high' : 'medium' }, r.severity) }, { label: 'Anomaly', render: (r) => h('div', null, h('div', { className: 'cell-title' }, r.title), h('div', { className: 'cell-sub' }, r.detail)) }, { label: 'Primary cause', key: 'primary_cause' }, { label: 'Added cost', right: true, render: (r) => money(r.estimated_additional_cost) }, { label: 'Status', render: (r) => h(Pill, { tone: 'neutral' }, r.status) }], rows: (d.anomalies || []).map((a) => ({ ...a, key: a.id })) })));
  return h('div', { className: 'metric-strip' }, (d.metrics || []).map((m) => h(Stat, { key: m.metric, label: m.metric, value: '$' + Number(m.value || 0).toFixed(m.value < 1 ? 4 : 2), note: `${money(m.numerator_cost)} / ${number(m.denominator_count)} · ${m.unit}` })));
}

function BudgetsPage({ tab, data, go }) {
  const [dashboard, governance, settings, anomalies] = data;
  const alerts = computeAlerts({ dashboard, governance, settings, anomalies });
  const g = governance, aws = g.aws || {}, k8s = g.kubernetes || {}, ai = g.ai || {}, s = dashboard.summary || {};
  const alertAt = Number((settings.settings || {}).alert_threshold || 80);
  if (tab === 'alerts') return h(Fragment, null,
    h('div', { className: 'gf-grid', style: { marginBottom: 18 } },
      h(Panel, { span: 3, title: 'Open alerts', info: 'Budget, anomaly and policy alerts' }, h(StatPanel, { value: alerts.length, display: number(alerts.length), thresholds: T.lowerIsBetter(1, 4), sub: 'computed from live thresholds' })),
      h(Panel, { span: 3, title: 'Cloud + AI budget', info: 'budgets.total in config.yaml' }, h(Gauge, { value: s.budget_utilization || 0, max: 120, decimals: 1, thresholds: T.lowerIsBetter(alertAt, 100), label: compact(s.total_monthly_spend) + ' of ' + compact(s.monthly_budget) })),
      h(Panel, { span: 3, title: 'AI budget', info: 'ai_finops.monthly_budget' }, h(Gauge, { value: ai.budget_utilization || 0, max: 150, decimals: 1, thresholds: T.lowerIsBetter(alertAt, 100), label: compact(ai.spend) + ' of ' + compact(ai.monthly_budget) })),
      h(Panel, { span: 3, title: 'Alert threshold', info: 'Set in Settings' }, h(StatPanel, { value: alertAt, display: alertAt + '%', color: 'var(--amber)', sub: 'warning line on every budget gauge' }))),
    h(Card, { title: 'Alerts', icon: 'bell' }, alerts.length ? alerts.map((a, i) => h('div', { className: 'alert-row', key: i }, h('span', { className: 'check-icon ' + a.tone, style: { width: 26, height: 26 } }, h(Icon, { name: 'alert', size: 14, stroke: 2.4 })), h('div', { style: { flex: 1 } }, h('div', { className: 'title' }, a.title), h('div', { className: 'sub' }, a.sub)), h('button', { className: 'btn ghost', onClick: () => go(a.page, a.tab) }, 'Open'))) : h('div', { className: 'empty' }, 'No alerts. Spend, budgets and policies are within thresholds.')));
  return h(Fragment, null,
    h('div', { className: 'gf-grid', style: { marginBottom: 18 } },
      h(Panel, { span: 3, title: 'AWS tag compliance', info: 'Average coverage of required tags' }, h(Gauge, { value: aws.overall, decimals: 1, thresholds: T.higherIsBetter(60, 85), label: 'tag coverage' })),
      h(Panel, { span: 3, title: 'K8s requests set', info: 'Workloads with CPU and memory requests' }, h(Gauge, { value: k8s.requests_compliance, decimals: 1, thresholds: T.higherIsBetter(70, 95), label: 'of workloads' })),
      h(Panel, { span: 3, title: 'K8s limits set', info: 'Workloads with limits' }, h(Gauge, { value: k8s.limits_compliance, decimals: 1, thresholds: T.higherIsBetter(70, 95), label: 'of workloads' })),
      h(Panel, { span: 3, title: 'AI budget used', info: 'AI spend / AI monthly budget' }, h(Gauge, { value: ai.budget_utilization, max: 150, decimals: 1, thresholds: T.lowerIsBetter(Number((settings.settings || {}).alert_threshold || 80), 100), label: money(ai.spend) + ' of ' + money(ai.monthly_budget) }))),
    h('div', { className: 'grid two' },
      h(Card, { title: 'Required tags', icon: 'shield', meta: 'From config.yaml' }, h('div', { className: 'tag-row', style: { marginBottom: 14 } }, (g.required_tags || []).map((t) => h('span', { className: 'tag', key: t }, t))), Object.entries(aws.by_tag || {}).map(([tag, v]) => h('div', { key: tag, style: { margin: '12px 0' } }, h('div', { style: { display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 6 } }, h('span', null, tag), h('strong', { className: 'num' }, pct(v))), h(Progress, { value: v, color: v >= 85 ? 'var(--green)' : 'var(--amber)' })))),
      h(Card, { title: 'Policy exceptions', icon: 'alert', iconTone: 'orange' }, h('div', { className: 'note' }, 'Workloads without requests'), h('div', { className: 'tag-row', style: { margin: '8px 0 16px' } }, (k8s.workloads_without_requests || []).map((w) => h('span', { className: 'tag', key: w }, w))), h('div', { className: 'note' }, 'Workloads without limits'), h('div', { className: 'tag-row', style: { margin: '8px 0 16px' } }, (k8s.workloads_without_limits || []).map((w) => h('span', { className: 'tag', key: w }, w))), h('div', { className: 'callout' }, 'AI spend is ', h('strong', null, pct(ai.budget_utilization)), ' of the ', h('strong', null, money(ai.monthly_budget)), ' monthly AI budget.'))),
    h(Card, { title: 'Untagged AWS resources', icon: 'server', className: 'gap-top' }, h(Table, { headers: [{ label: 'Resource', key: 'resource_id' }, { label: 'Type', key: 'resource_type' }, { label: 'Missing tags', render: (r) => h('div', { className: 'tag-row' }, r.missing_tags.map((t) => h('span', { className: 'tag', key: t }, t))) }], rows: (aws.resources || []).filter((r) => !r.compliant).map((r) => ({ ...r, key: r.resource_id })), empty: 'Every resource carries the required tags.' })));
}

function SettingsPage({ data, onSaved }) {
  const [d] = data;
  const [values, setValues] = useState(d.settings || {});
  const [msg, setMsg] = useState(null);
  useEffect(() => setValues(d.settings || {}), [d]);
  const fields = [['idle_cpu_threshold', 'AWS idle CPU threshold (%)', 0.5], ['idle_days', 'AWS idle window (days)', 1], ['old_snapshot_days', 'Snapshot age threshold (days)', 1], ['cpu_efficiency_threshold', 'K8s CPU efficiency threshold', 0.01], ['memory_efficiency_threshold', 'K8s memory efficiency threshold', 0.01], ['node_utilization_threshold', 'K8s node utilization threshold', 0.01], ['safety_margin', 'K8s rightsizing safety margin', 0.01], ['monthly_budget', 'AI monthly budget ($)', 100], ['alert_threshold', 'Budget alert threshold (%)', 1], ['high_cost_request', 'AI high-cost request ($)', 0.01], ['forecast_horizon_months', 'Forecast horizon (months)', 1], ['growth_rate', 'Forecast monthly growth', 0.01]];
  const save = async () => { setMsg(null); try { const r = await fetchJSON('/api/settings', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) }); onSaved([r]); setMsg({ tone: 'ok', text: 'Saved. All views now use the new thresholds.' }); } catch (e) { setMsg({ tone: 'error', text: e.message }); } };
  return h(Card, { title: 'Analysis thresholds', icon: 'settings', meta: 'PATCH /api/settings' },
    msg && h('div', { className: 'banner ' + (msg.tone === 'error' ? 'error' : ''), style: msg.tone === 'ok' ? { background: 'var(--green-soft)', borderColor: 'transparent' } : null }, msg.text),
    h('div', { className: 'form-grid' }, fields.map(([key, label, step]) => h('label', { className: 'field', key }, label, h('input', { type: 'number', step, value: values[key] ?? '', onChange: (e) => setValues({ ...values, [key]: e.target.value === '' ? '' : Number(e.target.value) }) })))),
    h('div', { style: { display: 'flex', gap: 12, alignItems: 'center', marginTop: 20, flexWrap: 'wrap' } }, h('button', { className: 'btn lg', onClick: save }, 'Save configuration'), h('span', { className: 'note' }, 'Written to config.yaml by the FastAPI backend. The GitHub Pages demo is read-only. Credentials are never entered here.')));
}

/* ---------------------------------------------------------------- modals */
function ExplainModal({ item, onClose }) {
  useEffect(() => { const k = (e) => e.key === 'Escape' && onClose(); window.addEventListener('keydown', k); return () => window.removeEventListener('keydown', k); }, [onClose]);
  if (!item) return null;
  return h('div', { className: 'overlay', onClick: onClose, role: 'dialog', 'aria-modal': 'true' }, h('div', { className: 'card modal', onClick: (e) => e.stopPropagation() },
    h('div', { className: 'card-head' }, h(Icon, { name: catIcon(item.category), className: 'head-icon' }), h('h2', null, 'Why this recommendation?'), h('button', { className: 'close', onClick: onClose, 'aria-label': 'Close' }, h(Icon, { name: 'x', size: 16 }))),
    h('div', { className: 'tag-row' }, h('span', { className: 'platform-badge ' + ({ AWS: 'aws', Kubernetes: 'k8s', AI: 'ai' }[item.platform] || '') }, item.platform), h(Pill, { tone: 'neutral' }, item.resource_id), h(Pill, { tone: 'neutral' }, item.confidence + ' confidence'), h(Pill, { tone: effortOf(item.risk) }, item.risk + ' risk')),
    h('p', null, h('strong', null, item.issue)), h('p', null, item.explanation),
    item.calculation && h('p', { className: 'note' }, h('strong', null, 'Calculation: '), item.calculation),
    h('div', { className: 'callout' }, h('strong', null, 'Estimated savings: ' + money2(item.estimated_monthly_savings) + ' / month. '), item.recommendation),
    h('p', { className: 'note' }, 'Source: ' + item.source + ' · Finding ID ' + item.id)));
}
function MethodModal({ onClose }) {
  return h('div', { className: 'overlay', onClick: onClose }, h('div', { className: 'card modal', onClick: (e) => e.stopPropagation() },
    h('div', { className: 'card-head' }, h(Icon, { name: 'book', className: 'head-icon' }), h('h2', null, 'Methodology'), h('button', { className: 'close', onClick: onClose, 'aria-label': 'Close' }, h(Icon, { name: 'x', size: 16 }))),
    h('p', null, h('strong', null, 'Measurement before remediation. '), 'Every finding carries an estimated monthly saving, a confidence level, a risk rating, its data source and a plain-language explanation. Nothing is applied automatically.'),
    h('p', null, h('strong', null, 'No double counting. '), 'Findings are keyed by platform + resource + category, and totals are summed over unique identities only.'),
    h('p', null, h('strong', null, 'Kubernetes allocation. '), 'Node cost is split into CPU and memory, charged to workloads by requests, and rolled up to namespaces. Unallocated cost stays visible and is never treated as savings.'),
    h('p', null, h('strong', null, 'AI unit economics. '), 'Usage is normalised across providers. Cost per 1K tokens = cost ÷ total tokens × 1,000. Model routing, caching and context reduction are evaluations that must be validated for quality.')));
}

/* ---------------------------------------------------------------- app shell */
const PAGES = {
  overview: { label: 'Overview', icon: 'home', tabs: null, load: () => loadAll(['/api/dashboard', '/api/forecast', '/api/governance', '/api/ai/overview', '/api/settings', '/api/recommendations']) },
  metrics: { label: 'Metrics', icon: 'gauge', title: 'Metrics', sub: 'Grafana-style panels: time series, bar charts, gauges and bar gauges over the same engine data.', tabs: [['3', 'Last 3 months'], ['6', 'Last 6 months'], ['12', 'Last 12 months']], load: () => loadAll(['/api/dashboard', '/api/kubernetes/overview', '/api/ai/overview', '/api/governance', '/api/settings', '/api/waste']) },
  costs: { label: 'Cost Analytics', icon: 'chart', title: 'Cost analytics', sub: 'Where the money goes, what is wasted, and where spend is heading.', tabs: [['aws', 'AWS costs'], ['waste', 'Waste'], ['forecast', 'Forecast']], load: (t) => t === 'aws' ? loadAll(['/api/costs', '/api/cost-history']) : loadAll([{ waste: '/api/waste', forecast: '/api/forecast' }[t]]) },
  optimization: { label: 'Optimization', icon: 'zap', title: 'Optimization queue', sub: 'Deduplicated, explainable opportunities across AWS, Kubernetes and AI.', tabs: [['all', 'All'], ['aws', 'AWS'], ['kubernetes', 'Kubernetes'], ['ai', 'AI']], load: () => loadAll(['/api/recommendations']) },
  kubernetes: { label: 'Kubernetes', icon: 'cube', title: 'Kubernetes cost allocation', sub: 'Requests versus real usage, allocated to the namespaces and teams that create it.', tabs: [['overview', 'Overview'], ['workloads', 'Workloads'], ['namespaces', 'Namespaces'], ['nodes', 'Nodes']], load: (t) => loadAll([{ overview: '/api/kubernetes/overview', workloads: '/api/kubernetes/workloads', namespaces: '/api/kubernetes/namespaces', nodes: '/api/kubernetes/nodes' }[t]]) },
  ai: { label: 'AI Insights', icon: 'sparkles', title: 'AI inference economics', sub: 'Tokens, models and applications, tied back to cost and business units.', tabs: [['overview', 'Overview'], ['usage', 'Token usage'], ['models', 'Models'], ['applications', 'Applications'], ['anomalies', 'Anomalies'], ['unit', 'Unit economics']], load: (t) => t === 'overview' ? loadAll(['/api/ai/overview', '/api/ai/cost-history']) : loadAll([{ usage: '/api/ai/usage', models: '/api/ai/models', applications: '/api/ai/applications', anomalies: '/api/ai/anomalies', unit: '/api/ai/unit-economics' }[t]]) },
  budgets: { label: 'Budgets & Alerts', icon: 'bell', title: 'Budgets, alerts & governance', sub: 'Budget posture, open alerts and policy compliance in one place.', tabs: [['alerts', 'Alerts'], ['governance', 'Governance']], load: () => loadAll(['/api/dashboard', '/api/governance', '/api/settings', '/api/ai/anomalies']) },
  settings: { label: 'Settings', icon: 'settings', title: 'Settings', sub: 'Thresholds in config.yaml drive every calculation in the engine.', tabs: null, load: () => loadAll(['/api/settings']) },
};

function parseHash() {
  const [page = 'overview', tab, filter] = (window.location.hash || '').replace(/^#\/?/, '').split('/');
  const p = PAGES[page] ? page : 'overview';
  const tabs = PAGES[p].tabs;
  return { page: p, tab: tabs ? (tabs.some(([k]) => k === tab) ? tab : (p === 'metrics' ? '12' : tabs[0][0])) : null, filter: filter ? decodeURIComponent(filter) : null };
}
function readTheme() { try { return localStorage.getItem('finops-theme'); } catch (e) { return null; } }
function writeTheme(v) { try { localStorage.setItem('finops-theme', v); } catch (e) { /* storage unavailable */ } }

function App() {
  const [route, setRoute] = useState(parseHash);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState(null);
  const [alertCount, setAlertCount] = useState(0);
  const [period, setPeriod] = useState('');
  const [explain, setExplain] = useState(null);
  const [method, setMethod] = useState(false);
  const [query, setQuery] = useState('');
  const [menu, setMenu] = useState(false);
  const [theme, setTheme] = useState(() => readTheme() || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));

  useEffect(() => { document.documentElement.setAttribute('data-theme', theme); writeTheme(theme); }, [theme]);
  useEffect(() => { const on = () => setRoute(parseHash()); window.addEventListener('hashchange', on); return () => window.removeEventListener('hashchange', on); }, []);
  const go = useCallback((page, tab, filter) => { window.location.hash = '/' + [page, tab, filter && encodeURIComponent(filter)].filter(Boolean).join('/'); setMenu(false); }, []);

  const loadShell = useCallback(async () => {
    try {
      const [m, dashboard, governance, settings, anomalies] = await loadAll(['/api/mode', '/api/dashboard', '/api/governance', '/api/settings', '/api/ai/anomalies']);
      setMode({ ...m, static: STATIC_MODE });
      setAlertCount(computeAlerts({ dashboard, governance, settings, anomalies }).length);
      const hist = dashboard.history || []; if (hist.length) setPeriod(hist[hist.length - 1].period);
    } catch (e) { /* page-level loader reports errors */ }
  }, []);
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setData(await PAGES[route.page].load(route.tab)); } catch (e) { setError(e.message || 'Unable to load data.'); setData(null); } finally { setLoading(false); }
  }, [route.page, route.tab]);
  useEffect(() => { loadShell(); }, [loadShell]);
  useEffect(() => { load(); }, [load]);

  const onSearch = (e) => { e.preventDefault(); go('optimization', 'all'); };
  const page = PAGES[route.page];
  const body = () => {
    if (loading) return h('div', { className: 'grid kpis' }, [0, 1, 2, 3].map((i) => h('div', { key: i, className: 'skeleton' })));
    if (error) return h('div', { className: 'banner error' }, h(Icon, { name: 'alert', size: 18 }), h('div', null, h('strong', null, 'Data unavailable. '), error));
    if (!data) return null;
    const props = { tab: route.tab, data, go, onExplain: setExplain };
    switch (route.page) {
      case 'overview': return h(Overview, props);
      case 'metrics': return h(MetricsPage, props);
      case 'costs': return h(CostsPage, props);
      case 'optimization': return h(OptimizationPage, { ...props, filter: route.filter, query });
      case 'kubernetes': return h(KubernetesPage, props);
      case 'ai': return h(AIPage, props);
      case 'budgets': return h(BudgetsPage, props);
      case 'settings': return h(SettingsPage, { data, onSaved: (d) => { setData(d); loadShell(); } });
      default: return null;
    }
  };
  const initials = PROFILE.name.split(' ').map((p) => p[0]).join('').slice(0, 2).toUpperCase();

  return h('div', { className: 'app' },
    h('aside', { className: 'sidebar ' + (menu ? 'open' : '') },
      h('div', { className: 'brand' }, h(Logo), h('div', { className: 'brand-title' }, 'FinOps AI', h('br'), 'Control Plane')),
      h('nav', { className: 'nav', 'aria-label': 'Main' }, Object.entries(PAGES).map(([key, p]) => h('button', { key, className: 'nav-item ' + (route.page === key ? 'active' : ''), onClick: () => go(key), 'aria-current': route.page === key ? 'page' : undefined }, h(Icon, { name: p.icon }), p.label, key === 'budgets' && alertCount > 0 && h('span', { className: 'count' }, alertCount)))),
      h('div', { className: 'promo', style: { marginTop: 28 } }, h(Icon, { name: 'leaf', size: 30, className: 'head-icon' }), h('h3', null, 'Show your math.'), h('p', null, 'Every saving carries its confidence, risk and source. Nothing is auto-applied.'), h('button', { className: 'btn ghost', onClick: () => setMethod(true) }, 'Methodology', h(Icon, { name: 'arrowRight', size: 14 }))),
      h('div', { className: 'profile' }, h('div', { className: 'avatar' }, initials), h('div', null, h('div', { className: 'profile-name' }, PROFILE.name), h('div', { className: 'profile-role' }, PROFILE.role)))),
    h('main', { className: 'main' },
      h('header', { className: 'topbar' },
        h('button', { className: 'chip icon-only menu-btn', onClick: () => setMenu(!menu), 'aria-label': 'Menu' }, h(Icon, { name: 'menu', size: 18 })),
        h('form', { className: 'search', onSubmit: onSearch, role: 'search' }, h(Icon, { name: 'search', size: 18 }), h('input', { value: query, onChange: (e) => setQuery(e.target.value), placeholder: 'Search findings, resources, or services…', 'aria-label': 'Search findings' })),
        h('div', { className: 'top-actions' },
          h('button', { className: 'chip icon-only', onClick: () => setTheme(theme === 'dark' ? 'light' : 'dark'), 'aria-label': 'Toggle theme', title: 'Toggle theme' }, h(Icon, { name: theme === 'dark' ? 'moon' : 'sun', size: 18, className: 'head-icon orange' })),
          h('div', { className: 'chip hide-sm', title: 'Platforms covered' }, h('span', { className: 'platform-badge aws' }, 'AWS'), h('span', { className: 'platform-badge k8s' }, 'K8s'), h('span', { className: 'platform-badge ai' }, 'AI')),
          h('div', { className: 'chip hide-sm', title: mode && mode.static ? 'Static demo fixtures' : 'Engine mode' }, h('span', { className: 'mode-dot' }), h('strong', null, mode ? (mode.static ? 'STATIC DEMO' : String(mode.mode).toUpperCase()) : '…')),
          period && h('div', { className: 'chip' }, h(Icon, { name: 'calendar', size: 16 }), periodLabel(period, true)),
          h('button', { className: 'chip icon-only', onClick: () => { load(); loadShell(); }, 'aria-label': 'Refresh', title: 'Refresh' }, h(Icon, { name: 'refresh', size: 17 })))),
      route.page !== 'overview' && h('div', { className: 'page-head' }, h('div', null, h('h1', null, page.title), h('p', null, page.sub)), page.tabs && h(Tabs, { tabs: page.tabs, active: route.tab, onChange: (t) => go(route.page, t) })),
      route.page !== 'overview' && data && !loading && h(Warnings, { warnings: data[0] && data[0].warnings }),
      body()),
    explain && h(ExplainModal, { item: explain, onClose: () => setExplain(null) }),
    method && h(MethodModal, { onClose: () => setMethod(false) }));
}

ReactDOM.createRoot(document.getElementById('root')).render(h(App));
