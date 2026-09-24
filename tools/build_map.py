#!/usr/bin/env python3
"""
Generate assets/world.svg from Natural Earth data (world-atlas topojson).

Produces a static SVG — no runtime JS or mapping library needed by the site.

Usage:
    curl -sL -o /tmp/countries-110m.json \
        https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json
    python3 tools/build_map.py /tmp/countries-110m.json assets/world.svg
"""

import json
import math
import sys

# Countries with a direct operating presence.
# label_dx/dy nudge the caption clear of the marker and neighbouring coastlines.
HIGHLIGHT = {
    "South Africa": {"label": "South Africa", "dx": 4, "dy": 26, "anchor": "middle"},
    "Botswana": {"label": "Botswana", "dx": -12, "dy": -14, "anchor": "end"},
    "United Kingdom": {"label": "United Kingdom", "dx": -14, "dy": -10, "anchor": "end"},
    "India": {"label": "India", "dx": 14, "dy": 5, "anchor": "start"},
}

STYLE = """
  .c { fill: #151b24; stroke: #222b38; stroke-width: .6; }
  .on { fill: url(#hl); stroke: #6ee7b7; stroke-width: .9; }
  .pin { fill: #f2fffa; stroke: #0b1016; stroke-width: .7; }
  .halo { fill: none; stroke: #f2fffa; stroke-width: 1.4; opacity: .9;
          transform-box: fill-box; transform-origin: center;
          animation: ping 2.8s cubic-bezier(.22,.61,.36,1) infinite; }
  .halo.b { animation-delay: .7s; }
  .halo.c2 { animation-delay: 1.4s; }
  .halo.d { animation-delay: 2.1s; }
  .lbl { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
         font-size: 13px; fill: #cfe9dd; letter-spacing: .04em; }
  @keyframes ping {
    0%   { transform: scale(.4); opacity: .9; }
    70%  { transform: scale(2.6); opacity: 0; }
    100% { transform: scale(2.6); opacity: 0; }
  }
  @media (prefers-reduced-motion: reduce) { .halo { animation: none; opacity: .35; } }
"""

WIDTH = 1000.0
# Vertical framing bounds. These must sit OUTSIDE the latitude range of any
# drawn geometry: clamping coordinates to the bounds collapses clipped polygon
# edges into straight horizontal streaks across the map. Antarctica is dropped
# separately, so the real extremes are ~83.6N (Greenland) and ~55.9S (Chile).
LAT_MAX = 84.0
LAT_MIN = -57.0


def decode_arcs(topo):
    """Delta-decode topojson arcs into absolute lon/lat coordinates."""
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    out = []
    for arc in topo["arcs"]:
        x = y = 0
        points = []
        for dx, dy in arc:
            x += dx
            y += dy
            points.append((x * sx + tx, y * sy + ty))
        out.append(points)
    return out


def ring_coords(arc_indices, arcs):
    """Stitch arc indices (negative = reversed) into one ring."""
    coords = []
    for idx in arc_indices:
        if idx < 0:
            pts = arcs[~idx][::-1]
        else:
            pts = arcs[idx]
        coords.extend(pts if not coords else pts[1:])
    return unwrap_antimeridian(coords)


def unwrap_antimeridian(pts):
    """Stop dateline-crossing rings from drawing a line across the whole map.

    Russia and Fiji have rings that step from roughly +179 to -179 longitude.
    Projected naively, that single step spans the full canvas width and renders
    as a horizontal streak. Shifting the negative longitudes by +360 keeps each
    ring continuous; the overflow past the right edge is clipped by the viewBox.
    """
    crosses = any(
        abs(pts[i][0] - pts[i - 1][0]) > 180 for i in range(1, len(pts))
    )
    if not crosses:
        return pts
    return [(lon + 360.0 if lon < 0 else lon, lat) for lon, lat in pts]


def project(lon, lat):
    """Project lon/lat into SVG space. Deliberately does NOT clamp latitude."""
    x = (lon + 180.0) / 360.0 * WIDTH
    y_top = _merc_y(LAT_MAX)
    y_bot = _merc_y(LAT_MIN)
    y = (_merc_y(lat) - y_top) / (y_bot - y_top) * _height()
    return x, y


def _merc_y(lat):
    """Mild Mercator-style vertical easing — keeps Africa/Europe readable."""
    rad = math.radians(lat)
    return math.log(math.tan(math.pi / 4 + rad / 2))


def _height():
    span = _merc_y(LAT_MIN) - _merc_y(LAT_MAX)
    # Keep aspect ratio proportional to the horizontal scale.
    return abs(span) / (2 * math.pi) * WIDTH


def centroid(geom, arcs):
    """Area-weighted centroid of the largest ring — where the marker sits."""
    polys = geom["arcs"] if geom["type"] == "MultiPolygon" else [geom["arcs"]]
    best_area, best = 0.0, (0.0, 0.0)
    for poly in polys:
        pts = [project(*p) for p in ring_coords(poly[0], arcs)]
        if len(pts) < 3:
            continue
        a = cx = cy = 0.0
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            cross = x0 * y1 - x1 * y0
            a += cross
            cx += (x0 + x1) * cross
            cy += (y0 + y1) * cross
        if abs(a) < 1e-9:
            continue
        area = abs(a / 2)
        if area > best_area:
            best_area = area
            best = (cx / (3 * a), cy / (3 * a))
    return best


def path_for(geom, arcs):
    parts = []
    polys = geom["arcs"] if geom["type"] == "MultiPolygon" else [geom["arcs"]]
    for poly in polys:
        for ring in poly:
            pts = ring_coords(ring, arcs)
            if len(pts) < 3:
                continue
            seg = []
            for i, (lon, lat) in enumerate(pts):
                x, y = project(lon, lat)
                seg.append(("M" if i == 0 else "L") + f"{x:.1f} {y:.1f}")
            parts.append("".join(seg) + "Z")
    return "".join(parts)


def main():
    src, dest = sys.argv[1], sys.argv[2]
    topo = json.load(open(src))
    arcs = decode_arcs(topo)
    height = _height()

    base, marks = [], []
    delay_class = ["", " b", " c2", " d"]
    found = 0

    for geom in topo["objects"]["countries"]["geometries"]:
        name = geom["properties"].get("name", "")
        if name == "Antarctica":
            continue
        d = path_for(geom, arcs)
        if not d:
            continue

        if name in HIGHLIGHT:
            cfg = HIGHLIGHT[name]
            base.append(f'<path class="c on" d="{d}"><title>{name}</title></path>')

            cx, cy = centroid(geom, arcs)
            halo_cls = delay_class[found % len(delay_class)]
            found += 1
            marks.append(
                f'<circle class="halo{halo_cls}" cx="{cx:.1f}" cy="{cy:.1f}" r="4"/>'
                f'<circle class="pin" cx="{cx:.1f}" cy="{cy:.1f}" r="3.4"/>'
                f'<text class="lbl" x="{cx + cfg["dx"]:.1f}" y="{cy + cfg["dy"]:.1f}" '
                f'text-anchor="{cfg["anchor"]}">{cfg["label"]}</text>'
            )
        else:
            base.append(f'<path class="c" d="{d}"/>')

    missing = set(HIGHLIGHT) - {
        g["properties"].get("name")
        for g in topo["objects"]["countries"]["geometries"]
    }
    if missing:
        raise SystemExit(f"ERROR: highlight countries not found in source data: {missing}")

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH:.0f} {height:.0f}" '
        f'role="img" aria-label="World map highlighting South Africa, Botswana, '
        f'the United Kingdom and India">',
        f"<style>{STYLE}</style>",
        '<defs><linearGradient id="hl" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#34d399"/>'
        '<stop offset="1" stop-color="#22d3ee"/>'
        "</linearGradient></defs>",
        "".join(base),
        "".join(marks),
        "</svg>",
    ]
    out = "".join(svg)
    open(dest, "w").write(out)
    print(
        f"wrote {dest} ({len(out):,} bytes, viewBox 0 0 {WIDTH:.0f} {height:.0f}, "
        f"{found} markers placed)"
    )


if __name__ == "__main__":
    main()
