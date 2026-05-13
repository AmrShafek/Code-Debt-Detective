"""
Graph Service
Manages dependency graph generation and visualization data preparation
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path


class GraphService:
    """Prepares and formats dependency graph data for visualization"""

    def __init__(self):
        self.graph_data = None

    def load_from_analysis(self, analysis_results: Dict[str, Any]):
        """Load graph data from analysis workflow results"""
        self.graph_data = analysis_results.get("details", {}).get("graph_json")

    def get_visjs_graph(self) -> Dict[str, Any]:
        """Format graph data for vis.js visualization"""
        if not self.graph_data:
            return {"nodes": [], "edges": []}

        graph = self.graph_data.get("graph", {})
        nodes = []
        for node in graph.get("nodes", []):
            nodes.append({
                "id": node.get("id"),
                "label": node.get("name", "").split(".")[-1][:20],
                "title": node.get("name", ""),
                "group": node.get("group", "unknown"),
                "value": node.get("size", 10),
                "instability": node.get("instability", 0.5)
            })

        edges = []
        for edge in graph.get("edges", []):
            edges.append({
                "from": edge.get("source"),
                "to": edge.get("target"),
                "arrows": "to",
                "color": {"color": "#848484"},
                "width": edge.get("weight", 1)
            })

        return {"nodes": nodes, "edges": edges}

    def get_d3_graph(self) -> Dict[str, Any]:
        """Format graph data for D3.js force-directed graph"""
        if not self.graph_data:
            return {"nodes": [], "links": []}

        graph = self.graph_data.get("graph", {})
        nodes = []
        for node in graph.get("nodes", []):
            nodes.append({
                "id": node.get("id"),
                "name": node.get("name", ""),
                "group": node.get("group", "unknown"),
                "instability": node.get("instability", 0.5)
            })

        links = []
        for edge in graph.get("edges", []):
            links.append({
                "source": edge.get("source"),
                "target": edge.get("target"),
                "value": edge.get("weight", 1)
            })

        return {"nodes": nodes, "links": links}

    def get_module_metrics(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract module metrics for visualization"""
        coupling_metrics = analysis_results.get("details", {}).get("coupling_metrics", {})
        module_metrics = coupling_metrics.get("module_metrics", {})

        result = []
        for module, metrics in module_metrics.items():
            result.append({
                "module": module,
                "afferent_coupling": metrics.get("afferent_coupling", 0),
                "efferent_coupling": metrics.get("efferent_coupling", 0),
                "instability": metrics.get("instability", 0),
                "classification": metrics.get("classification", "unknown")
            })

        return sorted(result, key=lambda x: x["instability"], reverse=True)

    def get_cycle_data(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract cyclic dependency data for visualization"""
        cycles = analysis_results.get("details", {}).get("cyclic_dependencies", {})
        return cycles.get("cycles", [])

    def summary_stats(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary statistics from graph data"""
        graph_data = self.graph_data or {}
        graph = graph_data.get("graph", {})
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "density": graph_data.get("density", 0),
            "has_cycles": analysis_results.get("details", {})
                .get("cyclic_dependencies", {}).get("has_cycles", False),
            "total_cycles": analysis_results.get("details", {})
                .get("cyclic_dependencies", {}).get("total_cycles", 0)
        }
