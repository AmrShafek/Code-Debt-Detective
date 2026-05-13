"""
Dependency graph visualization component using vis.js
"""

import json
import streamlit as st
from streamlit.components.v1 import html


def render_dependency_graph(graph_data: dict, height: int = 600):
    """Render an interactive dependency graph using vis.js

    Args:
        graph_data: Dict with 'nodes' and 'edges' lists
        height: Height of the graph container in pixels
    """
    if not graph_data or not graph_data.get("nodes"):
        st.info("No graph data available. Run an analysis first.")
        return

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)

    vis_html = f"""
    <div id="graph" style="height: {height}px; background: #1e1e1e; border-radius: 8px;"></div>
    <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js"></script>
    <script type="text/javascript">
        var nodes = new vis.DataSet({nodes_json});
        var edges = new vis.DataSet({edges_json});

        var container = document.getElementById('graph');
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        var options = {{
            nodes: {{
                shape: 'dot',
                size: 15,
                font: {{
                    color: '#ccc',
                    size: 12,
                    face: 'Monospace'
                }},
                borderWidth: 2,
                color: {{
                    background: '#2d7ff9',
                    border: '#1a5cc9',
                    highlight: {{
                        background: '#4d9fff',
                        border: '#2d7ff9'
                    }}
                }}
            }},
            edges: {{
                arrows: {{
                    to: {{ enabled: true, scaleFactor: 0.5 }}
                }},
                color: {{
                    color: '#555',
                    highlight: '#2d7ff9',
                    hover: '#2d7ff9',
                    opacity: 0.6
                }},
                smooth: {{
                    type: 'continuous'
                }}
            }},
            physics: {{
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {{
                    gravitationalConstant: -40,
                    centralGravity: 0.005,
                    springLength: 200,
                    springConstant: 0.08
                }},
                stabilization: {{
                    iterations: 200
                }}
            }},
            interaction: {{
                navigationButtons: true,
                keyboard: true,
                tooltipDelay: 100,
                hover: true
            }},
            layout: {{
                improvedLayout: true
            }}
        }};
        var network = new vis.Network(container, data, options);

        network.on("click", function(params) {{
            if (params.nodes.length > 0) {{
                var nodeId = params.nodes[0];
                var node = nodes.get(nodeId);
                if (node) {{
                    alert("Module: " + (node.title || node.label));
                }}
            }}
        }});
    </script>
    """

    html(vis_html, height=height + 40)


def render_mini_graph(graph_data: dict, height: int = 300):
    """Render a smaller version of the dependency graph"""
    render_dependency_graph(graph_data, height)
