"""
Teradata Code Parser
Extracts SQL and metadata from various file types
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ParsedFile:
    """Container for parsed file information"""
    file_path: str
    file_type: str  # 'sql', 'bteq', 'ksh', 'stored_proc'
    content: str
    sql_statements: List[Dict[str, any]]
    tables_referenced: List[str]
    metadata: Dict[str, any]


class TeradataCodeParser:
    """Parse Teradata code from various file formats"""
    
    # File extensions to process
    SQL_EXTENSIONS = ['.sql', '.bteq', '.btq']
    SCRIPT_EXTENSIONS = ['.ksh', '.sh', '.bash']
    
    # Teradata-specific patterns
    PATTERNS = {
        'create_table': re.compile(
            r'CREATE\s+(?:MULTISET\s+|SET\s+)?TABLE\s+(\w+\.\w+|\w+)',
            re.IGNORECASE
        ),
        'insert_into': re.compile(
            r'INSERT\s+INTO\s+(\w+\.\w+|\w+)',
            re.IGNORECASE
        ),
        'select_from': re.compile(
            r'FROM\s+(\w+\.\w+|\w+)',
            re.IGNORECASE
        ),
        'join': re.compile(
            r'(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+(\w+\.\w+|\w+)',
            re.IGNORECASE
        ),
        'update': re.compile(
            r'UPDATE\s+(\w+\.\w+|\w+)',
            re.IGNORECASE
        ),
        'merge_into': re.compile(
            r'MERGE\s+INTO\s+(\w+\.\w+|\w+)',
            re.IGNORECASE
        ),
        'bteq_logon': re.compile(
            r'\.LOGON\s+(\S+)',
            re.IGNORECASE
        ),
        'column_definition': re.compile(
            r'(\w+)\s+AS\s+(.+?)(?:,|\s+FROM|\s+WHERE|\)|$)',
            re.IGNORECASE | re.DOTALL
        )
    }
    
    def __init__(self, repo_path: Path):
        """
        Initialize parser
        
        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path)
    
    def parse_all_files(self) -> List[ParsedFile]:
        """
        Parse all relevant files in repository
        
        Returns:
            List of ParsedFile objects
        """
        parsed_files = []
        
        # Get all relevant files
        all_files = []
        all_files.extend(self.repo_path.rglob('*.sql'))
        all_files.extend(self.repo_path.rglob('*.bteq'))
        all_files.extend(self.repo_path.rglob('*.btq'))
        all_files.extend(self.repo_path.rglob('*.ksh'))
        all_files.extend(self.repo_path.rglob('*.sh'))
        
        for file_path in all_files:
            try:
                parsed = self.parse_file(file_path)
                if parsed:
                    parsed_files.append(parsed)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
        
        return parsed_files
    
    def parse_file(self, file_path: Path) -> Optional[ParsedFile]:
        """
        Parse a single file
        
        Args:
            file_path: Path to file
        
        Returns:
            ParsedFile object or None
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Cannot read {file_path}: {e}")
            return None
        
        # Determine file type
        suffix = file_path.suffix.lower()
        
        if suffix in ['.sql']:
            return self._parse_sql_file(file_path, content)
        elif suffix in ['.bteq', '.btq']:
            return self._parse_bteq_file(file_path, content)
        elif suffix in ['.ksh', '.sh', '.bash']:
            return self._parse_shell_script(file_path, content)
        
        return None
    
    def _parse_sql_file(self, file_path: Path, content: str) -> ParsedFile:
        """Parse standard SQL file"""
        sql_statements = self._extract_sql_statements(content)
        tables = self._extract_tables(content)
        
        return ParsedFile(
            file_path=str(file_path.relative_to(self.repo_path)),
            file_type='sql',
            content=content,
            sql_statements=sql_statements,
            tables_referenced=tables,
            metadata={
                'size': len(content),
                'line_count': content.count('\n') + 1
            }
        )
    
    def _parse_bteq_file(self, file_path: Path, content: str) -> ParsedFile:
        """Parse BTEQ script file"""
        # Extract BTEQ commands
        logon_match = self.PATTERNS['bteq_logon'].search(content)
        logon = logon_match.group(1) if logon_match else None
        
        # Remove BTEQ commands to get pure SQL
        sql_content = re.sub(r'^\s*\..*$', '', content, flags=re.MULTILINE)
        
        sql_statements = self._extract_sql_statements(sql_content)
        tables = self._extract_tables(sql_content)
        
        return ParsedFile(
            file_path=str(file_path.relative_to(self.repo_path)),
            file_type='bteq',
            content=content,
            sql_statements=sql_statements,
            tables_referenced=tables,
            metadata={
                'logon': logon,
                'size': len(content),
                'line_count': content.count('\n') + 1
            }
        )
    
    def _parse_shell_script(self, file_path: Path, content: str) -> ParsedFile:
        """Parse shell script with embedded SQL"""
        # Extract SQL from heredocs and bteq calls
        sql_blocks = []
        
        # Pattern for heredoc SQL
        heredoc_pattern = re.compile(
            r'<<\s*EOF.*?EOF',
            re.DOTALL | re.IGNORECASE
        )
        
        for match in heredoc_pattern.finditer(content):
            sql_blocks.append(match.group(0))
        
        # Pattern for SQL in quotes
        quoted_pattern = re.compile(
            r'["\']([^"\']*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|MERGE)[^"\']*)["\']',
            re.DOTALL | re.IGNORECASE
        )
        
        for match in quoted_pattern.finditer(content):
            sql_blocks.append(match.group(1))
        
        # Combine and parse SQL
        combined_sql = '\n'.join(sql_blocks)
        sql_statements = self._extract_sql_statements(combined_sql)
        tables = self._extract_tables(combined_sql)
        
        return ParsedFile(
            file_path=str(file_path.relative_to(self.repo_path)),
            file_type='ksh',
            content=content,
            sql_statements=sql_statements,
            tables_referenced=tables,
            metadata={
                'sql_blocks': len(sql_blocks),
                'size': len(content),
                'line_count': content.count('\n') + 1
            }
        )
    
    def _extract_sql_statements(self, content: str) -> List[Dict[str, any]]:
        """
        Extract individual SQL statements with metadata
        
        Args:
            content: SQL content
        
        Returns:
            List of statement dictionaries
        """
        statements = []
        
        # Split by semicolon (simple approach)
        raw_statements = content.split(';')
        
        for i, stmt in enumerate(raw_statements):
            stmt = stmt.strip()
            if not stmt or len(stmt) < 10:
                continue
            
            # Determine statement type
            stmt_type = self._get_statement_type(stmt)
            
            # Extract tables
            tables = self._extract_tables(stmt)
            
            # Extract columns (for SELECT statements)
            columns = self._extract_columns(stmt) if 'SELECT' in stmt.upper() else []
            
            statements.append({
                'statement_id': i,
                'type': stmt_type,
                'content': stmt,
                'tables': tables,
                'columns': columns,
                'length': len(stmt)
            })
        
        return statements
    
    def _get_statement_type(self, statement: str) -> str:
        """Determine SQL statement type"""
        stmt_upper = statement.upper().strip()
        
        if stmt_upper.startswith('SELECT'):
            return 'SELECT'
        elif stmt_upper.startswith('INSERT'):
            return 'INSERT'
        elif stmt_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif stmt_upper.startswith('DELETE'):
            return 'DELETE'
        elif stmt_upper.startswith('CREATE'):
            return 'CREATE'
        elif stmt_upper.startswith('MERGE'):
            return 'MERGE'
        elif stmt_upper.startswith('DROP'):
            return 'DROP'
        else:
            return 'OTHER'
    
    def _extract_tables(self, content: str) -> List[str]:
        """
        Extract all table names from SQL content
        
        Args:
            content: SQL content
        
        Returns:
            List of table names
        """
        tables = set()
        
        # Find all table references
        for pattern_name, pattern in self.PATTERNS.items():
            if pattern_name in ['bteq_logon', 'column_definition']:
                continue
            
            for match in pattern.finditer(content):
                table_name = match.group(1).strip()
                # Clean up table name
                table_name = re.sub(r'["\']', '', table_name)
                if table_name:
                    tables.add(table_name.upper())
        
        return sorted(list(tables))
    
    def _extract_columns(self, statement: str) -> List[Dict[str, str]]:
        """
        Extract column definitions from SELECT statement
        
        Args:
            statement: SELECT SQL statement
        
        Returns:
            List of column dictionaries
        """
        columns = []
        
        # Find SELECT ... FROM portion
        select_pattern = re.compile(
            r'SELECT\s+(.*?)\s+FROM',
            re.IGNORECASE | re.DOTALL
        )
        
        match = select_pattern.search(statement)
        if not match:
            return columns
        
        select_clause = match.group(1)
        
        # Find column definitions with AS
        for col_match in self.PATTERNS['column_definition'].finditer(select_clause):
            col_name = col_match.group(1).strip()
            col_expr = col_match.group(2).strip()
            
            columns.append({
                'name': col_name.upper(),
                'expression': col_expr
            })
        
        return columns
    
    def get_files_referencing_table(self, table_name: str, 
                                   parsed_files: List[ParsedFile]) -> List[ParsedFile]:
        """
        Find files that reference a specific table
        
        Args:
            table_name: Table name to search for
            parsed_files: List of parsed files
        
        Returns:
            List of files referencing the table
        """
        table_upper = table_name.upper()
        matching_files = []
        
        for parsed_file in parsed_files:
            if table_upper in [t.upper() for t in parsed_file.tables_referenced]:
                matching_files.append(parsed_file)
        
        return matching_files