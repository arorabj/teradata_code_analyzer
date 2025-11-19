"""
Lineage Visualizer
Creates visual representations of data lineage
"""

from typing import Dict
import html


class LineageVisualizer:
    """Create visualizations for lineage analysis"""
    
    def __init__(self):
        """Initialize visualizer"""
        pass
    
    def create_lineage_graph(self, lineage_result: Dict, 
                            table_name: str, column_name: str) -> str:
        """
        Create HTML visualization of lineage graph
        
        Args:
            lineage_result: Lineage analysis result
            table_name: Target table name
            column_name: Target column name
        
        Returns:
            HTML string for visualization
        """
        
        # Extract nodes and edges
        nodes = self._extract_nodes(lineage_result)
        edges = self._extract_edges(lineage_result)
        
        # Generate HTML with embedded SVG/D3.js visualization
        html_content = self._generate_html(nodes, edges, table_name, column_name)
        
        return html_content
    
    def _extract_nodes(self, lineage_result: Dict) -> list:
        """Extract nodes from lineage result"""
        nodes = []
        seen = set()
        
        # Add target
        target = lineage_result.get('target', {})
        target_id = f"{target.get('table', 'Target')}.{target.get('column', 'Column')}"
        
        if target_id not in seen:
            nodes.append({
                'id': target_id,
                'label': target_id,
                'type': 'target',
                'level': 0
            })
            seen.add(target_id)
        
        # Add from lineage chain
        for step in lineage_result.get('lineage_chain', []):
            table = step.get('table', 'Unknown')
            column = step.get('column', 'Unknown')
            node_id = f"{table}.{column}"
            
            if node_id not in seen:
                nodes.append({
                    'id': node_id,
                    'label': node_id,
                    'type': 'intermediate',
                    'level': step.get('level', 0),
                    'operation': step.get('operation', '')
                })
                seen.add(node_id)
        
        # Add source tables
        for source in lineage_result.get('source_tables', []):
            table = source.get('table_name', 'Unknown')
            
            for col in source.get('columns', ['*']):
                node_id = f"{table}.{col}"
                
                if node_id not in seen:
                    nodes.append({
                        'id': node_id,
                        'label': node_id,
                        'type': 'source',
                        'level': 999
                    })
                    seen.add(node_id)
        
        return nodes
    
    def _extract_edges(self, lineage_result: Dict) -> list:
        """Extract edges from lineage result"""
        edges = []
        
        lineage_chain = lineage_result.get('lineage_chain', [])
        
        for i in range(len(lineage_chain) - 1):
            source_step = lineage_chain[i]
            target_step = lineage_chain[i + 1]
            
            source_id = f"{source_step.get('table', 'Unknown')}.{source_step.get('column', 'Unknown')}"
            target_id = f"{target_step.get('table', 'Unknown')}.{target_step.get('column', 'Unknown')}"
            
            edges.append({
                'source': target_id,
                'target': source_id,
                'label': source_step.get('operation', '')
            })
        
        return edges
    
    def _generate_html(self, nodes: list, edges: list, 
                      table_name: str, column_name: str) -> str:
        """Generate HTML visualization"""
        
        # Create simple hierarchical layout
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .lineage-graph {{
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .node {{
            margin: 10px 0;
            padding: 15px;
            border-radius: 5px;
            position: relative;
        }}
        .node-target {{
            background-color: #FF6B35;
            color: white;
            font-weight: bold;
            font-size: 1.1em;
        }}
        .node-intermediate {{
            background-color: #FFA500;
            color: white;
            margin-left: 40px;
        }}
        .node-source {{
            background-color: #4CAF50;
            color: white;
            margin-left: 80px;
        }}
        .edge {{
            margin-left: 20px;
            padding: 5px;
            color: #666;
            font-style: italic;
        }}
        .node-details {{
            font-size: 0.9em;
            margin-top: 5px;
            opacity: 0.9;
        }}
        h2 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .legend {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }}
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
            padding: 5px 10px;
            border-radius: 3px;
            color: white;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="lineage-graph">
        <h2>📊 Data Lineage: {html.escape(table_name)}.{html.escape(column_name)}</h2>
        
        <div class="lineage-flow">
"""
        
        # Sort nodes by level
        sorted_nodes = sorted(nodes, key=lambda x: x.get('level', 0))
        
        # Render nodes
        for i, node in enumerate(sorted_nodes):
            node_type = node.get('type', 'intermediate')
            node_id = html.escape(node.get('id', ''))
            operation = node.get('operation', '')
            
            html += f"""
            <div class="node node-{node_type}">
                <div>{node_id}</div>
                {f'<div class="node-details">{html.escape(operation)}</div>' if operation else ''}
            </div>
"""
            
            # Add edge indicator
            if i < len(sorted_nodes) - 1:
                html += f"""
            <div class="edge">⬇️ derived from</div>
"""
        
        html += """
        </div>
        
        <div class="legend">
            <strong>Legend:</strong>
            <span class="legend-item" style="background-color: #FF6B35;">Target Column</span>
            <span class="legend-item" style="background-color: #FFA500;">Intermediate</span>
            <span class="legend-item" style="background-color: #4CAF50;">Source Tables</span>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def create_ascii_tree(self, lineage_result: Dict) -> str:
        """
        Create ASCII art tree representation
        
        Args:
            lineage_result: Lineage analysis result
        
        Returns:
            ASCII tree string
        """
        lines = []
        
        target = lineage_result.get('target', {})
        lines.append(f"📊 {target.get('table', 'Target')}.{target.get('column', 'Column')}")
        
        lineage_chain = lineage_result.get('lineage_chain', [])
        
        for i, step in enumerate(lineage_chain[1:], 1):
            indent = "  " * i
            table = step.get('table', 'Unknown')
            column = step.get('column', 'Unknown')
            operation = step.get('operation', '')
            
            lines.append(f"{indent}└── {table}.{column}")
            if operation:
                lines.append(f"{indent}    ({operation})")
        
        return "\n".join(lines)
    
    def export_to_mermaid(self, lineage_result: Dict) -> str:
        """
        Export lineage to Mermaid diagram format
        
        Args:
            lineage_result: Lineage analysis result
        
        Returns:
            Mermaid diagram syntax
        """
        lines = ["graph TD"]
        
        # Add nodes and edges
        lineage_chain = lineage_result.get('lineage_chain', [])
        
        for i, step in enumerate(lineage_chain):
            node_id = f"N{i}"
            label = f"{step.get('table', 'Unknown')}.{step.get('column', 'Unknown')}"
            
            if i == 0:
                lines.append(f"    {node_id}[\"{label}\"]")
                lines.append(f"    style {node_id} fill:#FF6B35,color:#fff")
            else:
                lines.append(f"    {node_id}[\"{label}\"]")
                lines.append(f"    N{i-1} --> |{step.get('operation', '')}| {node_id}")
        
        return "\n".join(lines)