"""
Lineage Analyzer
Uses RAG and LLM to analyze column lineage
"""

import json
import re
from typing import Dict, List, Optional


class LineageAnalyzer:
    """Analyze column lineage using RAG and LLM"""
    
    def __init__(self, rag_pipeline):
        """
        Initialize analyzer
        
        Args:
            rag_pipeline: LineageRAGPipeline instance
        """
        self.rag = rag_pipeline
    
    def analyze_column_lineage(self, table_name: str, column_name: str, 
                              max_depth: int = 5) -> Optional[Dict]:
        """
        Analyze lineage for a specific column
        
        Args:
            table_name: Target table name
            column_name: Target column name
            max_depth: Maximum depth to trace
        
        Returns:
            Dictionary with lineage information
        """
        print(f"Analyzing lineage for {table_name}.{column_name}")
        
        # Step 1: Find relevant code
        relevant_chunks = self._find_relevant_code(table_name, column_name)
        
        if not relevant_chunks:
            print("No relevant code found")
            return None
        
        print(f"Found {len(relevant_chunks)} relevant code chunks")
        
        # Step 2: Analyze with LLM
        lineage_result = self._analyze_with_llm(
            table_name,
            column_name,
            relevant_chunks,
            max_depth
        )
        
        return lineage_result
    
    def _find_relevant_code(self, table_name: str, column_name: str) -> List:
        """Find code chunks relevant to table and column"""
        
        # Search queries
        queries = [
            f"{table_name} {column_name}",
            f"INSERT INTO {table_name}",
            f"CREATE TABLE {table_name}",
            f"SELECT {column_name}",
            table_name
        ]
        
        all_chunks = []
        seen_ids = set()
        
        for query in queries:
            chunks = self.rag.retrieve(query, top_k=5)
            
            for chunk in chunks:
                if chunk.chunk_id not in seen_ids:
                    # Check if table is actually mentioned
                    if table_name.upper() in chunk.content.upper():
                        all_chunks.append(chunk)
                        seen_ids.add(chunk.chunk_id)
        
        return all_chunks
    
    def _analyze_with_llm(self, table_name: str, column_name: str,
                         chunks: List, max_depth: int) -> Dict:
        """Use LLM to analyze lineage from code chunks"""
        
        # Prepare context from chunks
        context = self._prepare_context(chunks)
        
        # Create analysis prompt
        prompt = self._create_lineage_prompt(
            table_name,
            column_name,
            context,
            max_depth
        )
        
        # Query LLM
        response = self.rag.query_llm(prompt, max_tokens=4000)
        
        # Parse response
        lineage_result = self._parse_llm_response(response, table_name, column_name)
        
        return lineage_result
    
    def _prepare_context(self, chunks: List) -> str:
        """Prepare context from chunks"""
        context_parts = []
        
        for i, chunk in enumerate(chunks[:15]):  # Limit to avoid token limits
            context_parts.append(f"""
--- Code Chunk {i+1} ---
File: {chunk.metadata.get('file_path', 'Unknown')}
Type: {chunk.metadata.get('statement_type', 'Unknown')}
Tables: {', '.join(chunk.metadata.get('tables', []))}

{chunk.content}
""")
        
        return "\n".join(context_parts)
    
    def _create_lineage_prompt(self, table_name: str, column_name: str,
                              context: str, max_depth: int) -> str:
        """Create prompt for lineage analysis"""
        
        prompt = f"""You are a Teradata SQL expert analyzing data lineage. Your task is to trace how a specific column in a table is derived from source data.

TARGET COLUMN TO ANALYZE:
Table: {table_name}
Column: {column_name}

AVAILABLE CODE:
{context}

INSTRUCTIONS:
1. Analyze the provided Teradata code to understand how {column_name} in {table_name} is populated
2. Trace back through all transformations to identify:
   - Source tables and columns
   - SQL transformations (calculations, aggregations, CASE statements, etc.)
   - Join conditions
   - Filter conditions (WHERE clauses)
   - Any intermediate tables

3. Build a complete lineage chain showing:
   - Each step in the data flow
   - The SQL logic at each step
   - Which file contains each transformation

4. Provide your analysis in the following JSON format:

{{
  "summary": "Brief description of how the column is derived",
  "target": {{
    "table": "{table_name}",
    "column": "{column_name}"
  }},
  "lineage_chain": [
    {{
      "level": 1,
      "table": "TARGET_TABLE",
      "column": "TARGET_COLUMN",
      "operation": "INSERT/CREATE/UPDATE",
      "source_file": "path/to/file.sql",
      "code_snippet": "relevant SQL code",
      "line_number": 10
    }},
    {{
      "level": 2,
      "table": "INTERMEDIATE_TABLE",
      "column": "SOURCE_COLUMN",
      "operation": "SELECT with transformation",
      "transformation": "SUM(amount) AS total",
      "source_file": "path/to/file.sql",
      "code_snippet": "relevant SQL code"
    }}
  ],
  "source_tables": [
    {{
      "table_name": "SOURCE_TABLE_1",
      "columns": ["col1", "col2"],
      "join_type": "LEFT JOIN",
      "filter_conditions": "WHERE date > '2024-01-01'"
    }}
  ],
  "transformations": [
    {{
      "type": "aggregation",
      "expression": "SUM(amount)",
      "description": "Aggregates transaction amounts"
    }},
    {{
      "type": "calculation",
      "expression": "price * quantity",
      "description": "Calculates line total"
    }}
  ]
}}

IMPORTANT:
- If you cannot find the lineage, explain why
- Include actual SQL code snippets
- Be specific about file paths and line numbers when visible
- Trace back to the original source tables (no further transformations)
- Handle Teradata-specific syntax (QUALIFY, SAMPLE, COLLECT STATISTICS, etc.)

Provide your analysis:"""
        
        return prompt
    
    def _parse_llm_response(self, response: str, table_name: str, 
                           column_name: str) -> Dict:
        """Parse LLM response into structured format"""
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                return result
            except json.JSONDecodeError:
                pass
        
        # Fallback: Create basic structure from text response
        return {
            "summary": response[:500],
            "target": {
                "table": table_name,
                "column": column_name
            },
            "lineage_chain": [
                {
                    "level": 1,
                    "table": table_name,
                    "column": column_name,
                    "operation": "Unknown",
                    "source_file": "Not parsed",
                    "code_snippet": response[:1000]
                }
            ],
            "source_tables": [],
            "transformations": [],
            "raw_response": response
        }
    
    def validate_lineage(self, lineage_result: Dict) -> bool:
        """
        Validate lineage result
        
        Args:
            lineage_result: Lineage analysis result
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['summary', 'target', 'lineage_chain', 'source_tables']
        
        for field in required_fields:
            if field not in lineage_result:
                return False
        
        if not lineage_result['lineage_chain']:
            return False
        
        return True
    
    def get_upstream_tables(self, lineage_result: Dict) -> List[str]:
        """
        Extract list of all upstream tables
        
        Args:
            lineage_result: Lineage analysis result
        
        Returns:
            List of table names
        """
        tables = set()
        
        # From lineage chain
        for step in lineage_result.get('lineage_chain', []):
            if step.get('table'):
                tables.add(step['table'])
        
        # From source tables
        for source in lineage_result.get('source_tables', []):
            if source.get('table_name'):
                tables.add(source['table_name'])
        
        return sorted(list(tables))
    
    def get_transformations_summary(self, lineage_result: Dict) -> str:
        """
        Create summary of transformations
        
        Args:
            lineage_result: Lineage analysis result
        
        Returns:
            Summary text
        """
        transformations = lineage_result.get('transformations', [])
        
        if not transformations:
            return "No transformations identified"
        
        summary_parts = []
        for i, trans in enumerate(transformations):
            trans_type = trans.get('type', 'Unknown')
            expr = trans.get('expression', 'N/A')
            desc = trans.get('description', '')
            
            summary_parts.append(f"{i+1}. {trans_type}: {expr}")
            if desc:
                summary_parts.append(f"   {desc}")
        
        return "\n".join(summary_parts)