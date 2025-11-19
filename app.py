"""
Teradata Code Lineage RAG Application
Main Streamlit interface for analyzing column lineage from GitHub repositories
"""

import streamlit as st
import sys
from pathlib import Path

# Add local modules to path
sys.path.append(str(Path(__file__).parent))

from src.github_ingestion import GitHubIngestion
from src.code_parser import TeradataCodeParser
from src.rag_pipeline import LineageRAGPipeline
from src.lineage_analyzer import LineageAnalyzer
from src.visualizer import LineageVisualizer

# Page configuration
st.set_page_config(
    page_title="Teradata Lineage Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF6B35;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4A4A4A;
        margin-bottom: 2rem;
    }
    .lineage-box {
        background-color: #F0F2F6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .source-table {
        background-color: #E3F2FD;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .transformation {
        background-color: #FFF9C4;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.rag_pipeline = None
        st.session_state.repo_indexed = False
        st.session_state.repo_path = None


def sidebar_config():
    """Configure sidebar with repository settings"""
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/FF6B35/FFFFFF?text=Teradata+RAG", 
                 use_container_width=True)
        st.markdown("---")
        
        st.subheader("🔧 Configuration")
        
        # GitHub Repository Settings
        st.markdown("### GitHub Repository")
        repo_url = st.text_input(
            "Repository URL",
            value="https://github.com/your-org/teradata-code",
            help="Enter the GitHub repository URL containing Teradata code"
        )
        
        branch = st.text_input(
            "Branch",
            value="main",
            help="Branch to analyze"
        )
        
        github_token = st.text_input(
            "GitHub Token (Optional)",
            type="password",
            help="Personal access token for private repos"
        )
        
        # LLM Settings
        st.markdown("### LLM Configuration")
        llm_provider = st.selectbox(
            "Provider",
            ["AWS Bedrock", "Anthropic API"],
            help="Select LLM provider"
        )
        
        if llm_provider == "AWS Bedrock":
            aws_region = st.text_input("AWS Region", value="us-east-1")
            model_id = st.selectbox(
                "Model",
                ["anthropic.claude-3-sonnet-20240229-v1:0",
                 "anthropic.claude-3-5-sonnet-20241022-v2:0"]
            )
        else:
            api_key = st.text_input("Anthropic API Key", type="password")
            model_id = "claude-3-5-sonnet-20241022"
        
        # Index Repository Button
        st.markdown("---")
        if st.button("🔄 Index Repository", type="primary", use_container_width=True):
            return {
                'repo_url': repo_url,
                'branch': branch,
                'github_token': github_token if github_token else None,
                'llm_provider': llm_provider,
                'model_id': model_id,
                'aws_region': aws_region if llm_provider == "AWS Bedrock" else None,
                'api_key': api_key if llm_provider == "Anthropic API" else None,
                'index_action': True
            }
        
        # Statistics
        if st.session_state.repo_indexed:
            st.markdown("---")
            st.markdown("### 📊 Repository Stats")
            if st.session_state.rag_pipeline:
                stats = st.session_state.rag_pipeline.get_stats()
                st.metric("Total Files", stats.get('total_files', 0))
                st.metric("SQL Files", stats.get('sql_files', 0))
                st.metric("KSH Scripts", stats.get('ksh_files', 0))
                st.metric("BTEQ Scripts", stats.get('bteq_files', 0))
    
    return None


def index_repository(config):
    """Index the GitHub repository"""
    progress_container = st.container()
    
    with progress_container:
        with st.status("Indexing repository...", expanded=True) as status:
            try:
                # Step 1: Clone/Download Repository
                st.write("📥 Cloning repository...")
                ingestion = GitHubIngestion(
                    repo_url=config['repo_url'],
                    branch=config['branch'],
                    token=config.get('github_token')
                )
                repo_path = ingestion.clone_or_pull()
                st.session_state.repo_path = repo_path
                st.write(f"✅ Repository cloned to: {repo_path}")
                
                # Step 2: Parse Code Files
                st.write("🔍 Parsing Teradata code files...")
                parser = TeradataCodeParser(repo_path)
                parsed_files = parser.parse_all_files()
                st.write(f"✅ Parsed {len(parsed_files)} files")
                
                # Step 3: Build RAG Pipeline
                st.write("🧠 Building RAG pipeline...")
                rag_pipeline = LineageRAGPipeline(
                    llm_provider=config['llm_provider'],
                    model_id=config['model_id'],
                    aws_region=config.get('aws_region'),
                    api_key=config.get('api_key')
                )
                
                # Step 4: Index Documents
                st.write("📚 Creating vector embeddings...")
                rag_pipeline.index_documents(parsed_files)
                st.session_state.rag_pipeline = rag_pipeline
                st.write("✅ Vector index created")
                
                st.session_state.repo_indexed = True
                st.session_state.initialized = True
                
                status.update(label="✅ Repository indexed successfully!", state="complete")
                st.success("Repository is ready for lineage analysis!")
                
            except Exception as e:
                status.update(label="❌ Error during indexing", state="error")
                st.error(f"Error: {str(e)}")
                st.exception(e)


def main():
    """Main application"""
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🔍 Teradata Code Lineage Analyzer</div>', 
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Reverse Engineering of Teradata ETL Code</div>', 
                unsafe_allow_html=True)
    
    # Sidebar configuration
    sidebar_action = sidebar_config()
    
    # Handle repository indexing
    if sidebar_action and sidebar_action.get('index_action'):
        index_repository(sidebar_action)
    
    # Main content
    if not st.session_state.repo_indexed:
        st.info("👈 Configure and index a repository from the sidebar to begin analysis")
        
        # Show example
        with st.expander("📖 How to use this tool"):
            st.markdown("""
            ### Steps to Analyze Column Lineage:
            
            1. **Configure Repository** (in sidebar):
               - Enter your GitHub repository URL
               - Provide authentication if needed for private repos
               - Click "Index Repository"
            
            2. **Enter Table & Column**:
               - Specify the target table name
               - Specify the column you want to trace
            
            3. **Analyze**:
               - Click "Analyze Lineage" button
               - View complete lineage chain with transformations
            
            ### Supported File Types:
            - `.sql` - SQL scripts
            - `.bteq` - BTEQ scripts
            - `.ksh` - Shell scripts with embedded SQL
            - Stored procedures and macros
            
            ### Example Query:
            ```
            Table: CUSTOMER_SUMMARY
            Column: TOTAL_PURCHASES
            ```
            """)
        return
    
    # Lineage Analysis Interface
    st.markdown("---")
    st.subheader("📊 Analyze Column Lineage")
    
    col1, col2 = st.columns(2)
    
    with col1:
        table_name = st.text_input(
            "Table Name",
            placeholder="e.g., CUSTOMER_SUMMARY",
            help="Enter the target table name (case-insensitive)"
        )
    
    with col2:
        column_name = st.text_input(
            "Column Name",
            placeholder="e.g., TOTAL_PURCHASES",
            help="Enter the column name to trace"
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        max_depth = st.slider(
            "Maximum Lineage Depth",
            min_value=1,
            max_value=10,
            value=5,
            help="How many levels deep to trace lineage"
        )
        
        include_transformations = st.checkbox(
            "Include Transformation Details",
            value=True,
            help="Show SQL expressions and transformation logic"
        )
        
        show_code_snippets = st.checkbox(
            "Show Code Snippets",
            value=True,
            help="Display relevant code excerpts"
        )
    
    # Analyze button
    analyze_button = st.button(
        "🔍 Analyze Lineage",
        type="primary",
        use_container_width=True,
        disabled=not (table_name and column_name)
    )
    
    if analyze_button:
        analyze_lineage(
            table_name,
            column_name,
            max_depth,
            include_transformations,
            show_code_snippets
        )


def analyze_lineage(table_name, column_name, max_depth, 
                    include_transformations, show_code_snippets):
    """Perform lineage analysis"""
    
    with st.status("Analyzing lineage...", expanded=True) as status:
        try:
            # Initialize analyzer
            st.write("🔍 Searching codebase...")
            analyzer = LineageAnalyzer(st.session_state.rag_pipeline)
            
            # Perform analysis
            st.write("🧠 Analyzing with Claude...")
            lineage_result = analyzer.analyze_column_lineage(
                table_name=table_name,
                column_name=column_name,
                max_depth=max_depth
            )
            
            if not lineage_result:
                status.update(label="❌ No lineage found", state="error")
                st.error(f"Could not find lineage for {table_name}.{column_name}")
                return
            
            status.update(label="✅ Analysis complete!", state="complete")
            
            # Display results
            display_lineage_results(
                lineage_result,
                table_name,
                column_name,
                include_transformations,
                show_code_snippets
            )
            
        except Exception as e:
            status.update(label="❌ Error during analysis", state="error")
            st.error(f"Error: {str(e)}")
            st.exception(e)


def display_lineage_results(lineage_result, table_name, column_name,
                           include_transformations, show_code_snippets):
    """Display lineage analysis results"""
    
    st.markdown("---")
    st.markdown(f"## 📊 Lineage Analysis: `{table_name}.{column_name}`")
    
    # Summary
    st.markdown('<div class="lineage-box">', unsafe_allow_html=True)
    st.markdown("### 📝 Summary")
    st.write(lineage_result.get('summary', 'No summary available'))
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌳 Lineage Chain",
        "📦 Source Tables",
        "🔄 Transformations",
        "📊 Visualization"
    ])
    
    with tab1:
        display_lineage_chain(lineage_result, show_code_snippets)
    
    with tab2:
        display_source_tables(lineage_result)
    
    with tab3:
        if include_transformations:
            display_transformations(lineage_result)
        else:
            st.info("Enable 'Include Transformation Details' to see this section")
    
    with tab4:
        display_visualization(lineage_result, table_name, column_name)


def display_lineage_chain(lineage_result, show_code_snippets):
    """Display lineage chain"""
    st.markdown("### Lineage Chain")
    
    lineage_chain = lineage_result.get('lineage_chain', [])
    
    for i, step in enumerate(lineage_chain):
        with st.container():
            st.markdown(f"#### Level {i + 1}: {step.get('table', 'Unknown')}")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Column**: `{step.get('column', 'N/A')}`")
                st.markdown(f"**Operation**: {step.get('operation', 'N/A')}")
                
                if show_code_snippets and step.get('code_snippet'):
                    with st.expander("View Code Snippet"):
                        st.code(step['code_snippet'], language="sql")
            
            with col2:
                st.markdown(f"**File**: `{step.get('source_file', 'N/A')}`")
                st.markdown(f"**Line**: {step.get('line_number', 'N/A')}")
            
            if i < len(lineage_chain) - 1:
                st.markdown("⬇️")


def display_source_tables(lineage_result):
    """Display source tables"""
    st.markdown("### Source Tables")
    
    source_tables = lineage_result.get('source_tables', [])
    
    if not source_tables:
        st.info("No source tables identified")
        return
    
    for table in source_tables:
        st.markdown(f'<div class="source-table">', unsafe_allow_html=True)
        st.markdown(f"**{table.get('table_name', 'Unknown')}**")
        
        if table.get('columns'):
            st.markdown("Columns: " + ", ".join([f"`{c}`" for c in table['columns']]))
        
        if table.get('join_type'):
            st.markdown(f"Join Type: {table['join_type']}")
        
        if table.get('filter_conditions'):
            st.markdown(f"Filters: `{table['filter_conditions']}`")
        
        st.markdown('</div>', unsafe_allow_html=True)


def display_transformations(lineage_result):
    """Display transformations"""
    st.markdown("### Transformations")
    
    transformations = lineage_result.get('transformations', [])
    
    if not transformations:
        st.info("No transformations identified")
        return
    
    for i, transform in enumerate(transformations):
        st.markdown(f'<div class="transformation">', unsafe_allow_html=True)
        st.markdown(f"**Transformation {i + 1}**")
        st.markdown(f"**Type**: {transform.get('type', 'Unknown')}")
        st.markdown(f"**Expression**: `{transform.get('expression', 'N/A')}`")
        
        if transform.get('description'):
            st.markdown(f"**Description**: {transform['description']}")
        
        st.markdown('</div>', unsafe_allow_html=True)


def display_visualization(lineage_result, table_name, column_name):
    """Display lineage visualization"""
    st.markdown("### Lineage Graph")
    
    try:
        visualizer = LineageVisualizer()
        graph_html = visualizer.create_lineage_graph(
            lineage_result,
            table_name,
            column_name
        )
        
        st.components.v1.html(graph_html, height=600, scrolling=True)
        
    except Exception as e:
        st.warning(f"Could not generate visualization: {str(e)}")
        st.info("Displaying text-based lineage tree instead:")
        
        # Fallback: text-based tree
        display_text_tree(lineage_result)


def display_text_tree(lineage_result):
    """Display text-based lineage tree"""
    lineage_chain = lineage_result.get('lineage_chain', [])
    
    tree_text = f"📊 {lineage_chain[0].get('table', 'Target')}.{lineage_chain[0].get('column', 'Column')}\n"
    
    for i in range(1, len(lineage_chain)):
        step = lineage_chain[i]
        indent = "  " * i
        tree_text += f"{indent}└── {step.get('table', 'Unknown')}.{step.get('column', 'Unknown')}\n"
        
        if step.get('operation'):
            tree_text += f"{indent}    ({step['operation']})\n"
    
    st.code(tree_text, language="text")


if __name__ == "__main__":
    main()