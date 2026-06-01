#!/usr/bin/env python3
"""
launch_dashboard.py — Launch an interactive dashboard for exploring the knowledge graph.

Usage:
    python3 launch_dashboard.py <project-root> [--port 3000] [--graph <path>]

Starts a local HTTP server that serves an interactive web dashboard for the
knowledge graph produced by build_graph.py.
"""

import argparse
import json
import os
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Understand Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; }
.header { padding: 16px 24px; background: #161b22; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 16px; }
.header h1 { font-size: 18px; font-weight: 600; color: #58a6ff; }
.header .subtitle { font-size: 13px; color: #8b949e; }
.container { display: flex; height: calc(100vh - 53px); }
.sidebar { width: 320px; background: #161b22; border-right: 1px solid #30363d; overflow-y: auto; padding: 16px; }
.sidebar h2 { font-size: 13px; font-weight: 600; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
.layer { margin-bottom: 8px; }
.layer-header { padding: 8px 12px; background: #21262d; border-radius: 6px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
.layer-header:hover { background: #30363d; }
.layer-count { background: #30363d; padding: 2px 8px; border-radius: 10px; font-size: 11px; color: #8b949e; }
.layer-files { padding: 4px 0 4px 16px; display: none; }
.layer-files.open { display: block; }
.file-item { padding: 4px 8px; font-size: 12px; color: #8b949e; cursor: pointer; border-radius: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.file-item:hover { background: #21262d; color: #c9d1d9; }
.main { flex: 1; overflow-y: auto; padding: 24px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 24px; }
.stat-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
.stat-card .value { font-size: 28px; font-weight: 700; color: #58a6ff; }
.stat-card .label { font-size: 12px; color: #8b949e; margin-top: 4px; }
.section { margin-bottom: 24px; }
.section h2 { font-size: 16px; font-weight: 600; margin-bottom: 12px; color: #e6edf3; }
.tour-step { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin-bottom: 8px; }
.tour-step .step-num { display: inline-block; width: 24px; height: 24px; background: #238636; color: white; border-radius: 50%; text-align: center; line-height: 24px; font-size: 12px; font-weight: 600; margin-right: 8px; }
.tour-step .step-title { font-weight: 600; color: #e6edf3; }
.tour-step .step-desc { font-size: 13px; color: #8b949e; margin-top: 4px; }
.search-box { width: 100%; padding: 8px 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-size: 13px; margin-bottom: 16px; }
.search-box:focus { outline: none; border-color: #58a6ff; }
.tag { display: inline-block; padding: 2px 8px; background: #1f6feb33; color: #58a6ff; border-radius: 12px; font-size: 11px; margin-right: 4px; }
</style>
</head>
<body>
<div class="header">
  <h1>🔍 Understand Dashboard</h1>
  <span class="subtitle" id="project-name">Loading...</span>
</div>
<div class="container">
  <div class="sidebar">
    <h2>Search</h2>
    <input type="text" class="search-box" placeholder="Search files..." id="search" oninput="filterFiles()">
    <h2>Layers</h2>
    <div id="layers"></div>
  </div>
  <div class="main">
    <div class="stats" id="stats"></div>
    <div class="section">
      <h2>📊 Project Info</h2>
      <div id="project-info"></div>
    </div>
    <div class="section">
      <h2>🧭 Guided Tour</h2>
      <div id="tour"></div>
    </div>
  </div>
</div>
<script>
let graph = null;

async function loadGraph() {
  const resp = await fetch('/graph.json');
  graph = await resp.json();
  render();
}

function render() {
  if (!graph) return;
  document.getElementById('project-name').textContent = graph.project?.name || 'Unknown Project';

  // Stats
  const stats = graph.stats || {};
  document.getElementById('stats').innerHTML = `
    <div class="stat-card"><div class="value">${graph.nodes?.length || 0}</div><div class="label">Nodes</div></div>
    <div class="stat-card"><div class="value">${graph.edges?.length || 0}</div><div class="label">Edges</div></div>
    <div class="stat-card"><div class="value">${graph.layers?.length || 0}</div><div class="label">Layers</div></div>
    <div class="stat-card"><div class="value">${graph.tour?.length || 0}</div><div class="label">Tour Steps</div></div>
  `;

  // Project info
  const p = graph.project || {};
  document.getElementById('project-info').innerHTML = `
    <p style="margin-bottom:8px;color:#8b949e;">${p.description || 'No description'}</p>
    <div>${(p.languages || []).map(l => `<span class="tag">${l}</span>`).join('')}</div>
    <div style="margin-top:4px;">${(p.frameworks || []).map(f => `<span class="tag">${f}</span>`).join('')}</div>
  `;

  // Layers
  const layersEl = document.getElementById('layers');
  layersEl.innerHTML = (graph.layers || []).map(l => `
    <div class="layer">
      <div class="layer-header" onclick="toggleLayer(this)">
        <span>${l.name}</span>
        <span class="layer-count">${l.nodeIds?.length || 0}</span>
      </div>
      <div class="layer-files">
        ${(l.nodeIds || []).slice(0, 20).map(n => {
          const name = n.replace('file:', '').replace('config:', '').replace('document:', '').replace('service:', '').replace('pipeline:', '');
          return `<div class="file-item" title="${n}">${name}</div>`;
        }).join('')}
      </div>
    </div>
  `).join('');

  // Tour
  document.getElementById('tour').innerHTML = (graph.tour || []).map(t => `
    <div class="tour-step">
      <span class="step-num">${t.order}</span>
      <span class="step-title">${t.title}</span>
      <div class="step-desc">${t.description}</div>
    </div>
  `).join('');
}

function toggleLayer(el) {
  const files = el.nextElementSibling;
  files.classList.toggle('open');
}

function filterFiles() {
  const q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('.file-item').forEach(el => {
    el.style.display = el.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

loadGraph();
</script>
</body>
</html>
"""


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/graph.json':
            graph_path = self.server.graph_path
            if graph_path.exists():
                content = graph_path.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, 'Graph not found')
        elif parsed.path == '/':
            content = DASHBOARD_HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # Suppress logs


def main():
    parser = argparse.ArgumentParser(description="Launch knowledge graph dashboard")
    parser.add_argument("project_root", help="Path to the project root")
    parser.add_argument("--port", type=int, default=3000, help="Port to serve on")
    parser.add_argument("--graph", help="Path to knowledge-graph.json")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    graph_path = Path(args.graph) if args.graph else root / ".understand" / "knowledge-graph.json"

    if not graph_path.exists():
        print(f"Error: Knowledge graph not found at {graph_path}", file=sys.stderr)
        print("Run build_graph.py first to generate the graph.", file=sys.stderr)
        sys.exit(1)

    server = HTTPServer(('127.0.0.1', args.port), DashboardHandler)
    server.graph_path = graph_path

    url = f"http://127.0.0.1:{args.port}"
    print(f"Dashboard running at {url}", file=sys.stderr)
    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", file=sys.stderr)
        server.shutdown()


if __name__ == "__main__":
    main()
