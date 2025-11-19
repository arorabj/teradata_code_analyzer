# Teradata Code Lineage RAG System

**AI-Powered Reverse Engineering of Teradata ETL Code**

Automatically trace column lineage from your Teradata codebase using LLM-powered semantic analysis. No more manual lineage documentation!

---

## 🎯 Features

- **Automated Lineage Analysis**: Trace any column back to its source tables
- **Multi-Format Support**: Parses `.sql`, `.bteq`, and `.ksh` (shell scripts)
- **Teradata-Specific**: Handles BTEQ, multi-statement requests, QUALIFY, SAMPLE, and more
- **RAG Architecture**: Semantic search through your entire codebase
- **Claude 3.5 Sonnet**: Powered by state-of-the-art reasoning
- **Visual Lineage**: Interactive graphs and dependency trees
- **SageMaker Ready**: Designed for AWS SageMaker Studio deployment

---

## 🏗️ Architecture

```
┌─────────────────┐
│  GitHub Repo    │
│  (Teradata Code)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Code Parser     │
│ • .sql files    │
│ • .bteq scripts │
│ • .ksh scripts  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vector Store    │
│ (FAISS Index)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RAG Pipeline    │
│ Retrieval +     │
│ Claude 3.5      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Lineage Result  │
│ • Source tables │
│ • Transforms    │
│ • Visualization │
└─────────────────┘
```

---

## 📁 Project Structure

```
teradata-lineage-rag/
├── app.py                          # Main Streamlit application
├── src/
│   ├── __init__.py
│   ├── github_ingestion.py         # GitHub repo cloning/management
│   ├── code_parser.py              # Parse SQL/BTEQ/KSH files
│   ├── rag_pipeline.py             # RAG + Vector DB + LLM
│   ├── lineage_analyzer.py         # Lineage analysis logic
│   └── visualizer.py               # Lineage visualization
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── .gitignore
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Git installed
- AWS credentials (for Bedrock) OR Anthropic API key
- Access to a GitHub repository with Teradata code

### Installation

#### Option 1: AWS SageMaker Studio

1. **Open SageMaker Studio**
2. **Launch Terminal**
3. **Clone this repository**:
   ```bash
   git clone https://github.com/your-org/teradata-lineage-rag.git
   cd teradata-lineage-rag
   ```

4. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

6. **Create src directory structure**:
   ```bash
   mkdir -p src
   touch src/__init__.py
   ```

7. **Run the application**:
   ```bash
   streamlit run app.py --server.port 8501
   ```

8. **Access the UI**: Click the preview link in SageMaker Studio

#### Option 2: Local Development

1. **Clone repository**:
   ```bash
   git clone https://github.com/your-org/teradata-lineage-rag.git
   cd teradata-lineage-rag
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up credentials**:
   
   **For AWS Bedrock**:
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_DEFAULT_REGION=us-east-1
   ```
   
   **For Anthropic API**:
   ```bash
   export ANTHROPIC_API_KEY=your_api_key
   ```

5. **Run the app**:
   ```bash
   streamlit run app.py
   ```

6. **Open browser**: Navigate to http://localhost:8501

---

## 📖 Usage Guide

### Step 1: Configure Repository

1. Open the Streamlit app
2. In the sidebar, enter:
   - **Repository URL**: Your GitHub repo (e.g., `https://github.com/your-org/teradata-etl`)
   - **Branch**: Usually `main` or `master`
   - **GitHub Token**: (Optional) For private repos
3. Configure LLM:
   - **AWS Bedrock**: Select region and model
   - **Anthropic API**: Enter your API key
4. Click **"Index Repository"**

The app will:
- Clone the repository
- Parse all `.sql`, `.bteq`, and `.ksh` files
- Extract SQL statements and metadata
- Build vector embeddings
- Create searchable index

### Step 2: Analyze Column Lineage

1. Enter the **Table Name** (e.g., `CUSTOMER_SUMMARY`)
2. Enter the **Column Name** (e.g., `TOTAL_PURCHASES`)
3. (Optional) Adjust advanced options:
   - Maximum lineage depth
   - Show transformation details
   - Display code snippets
4. Click **"Analyze Lineage"**

### Step 3: Review Results

The app displays:

- **📝 Summary**: High-level description of how the column is derived
- **🌳 Lineage Chain**: Step-by-step data flow from source to target
- **📦 Source Tables**: All upstream tables with columns and join conditions
- **🔄 Transformations**: SQL expressions, aggregations, calculations
- **📊 Visualization**: Interactive lineage graph

---

## 🔍 Example Query

**Input:**
```
Table Name: ACCOUNT_BALANCE
Column Name: AVAILABLE_BALANCE
```

**Output:**
```
Summary: AVAILABLE_BALANCE is calculated as CURRENT_BALANCE minus PENDING_TRANSACTIONS 
from ACCOUNT_MASTER and TRANSACTION_PENDING tables.

Lineage Chain:
  Level 1: ACCOUNT_BALANCE.AVAILABLE_BALANCE
           ⬇️ (INSERT via stored_proc.sql)
  Level 2: ACCOUNT_MASTER.CURRENT_BALANCE
           TRANSACTION_PENDING.PENDING_AMOUNT
           ⬇️ (LEFT JOIN + SUM aggregation)
  Level 3: RAW_ACCOUNTS.BALANCE
           RAW_TRANSACTIONS.AMOUNT

Source Tables:
  • RAW_ACCOUNTS (BALANCE, ACCOUNT_ID)
  • RAW_TRANSACTIONS (AMOUNT, ACCOUNT_ID, STATUS)

Transformations:
  1. Aggregation: SUM(PENDING_AMOUNT)
  2. Calculation: CURRENT_BALANCE - COALESCE(PENDING_AMOUNT, 0)
```

---

## 🛠️ Configuration

### LLM Configuration

#### AWS Bedrock

Recommended models:
- `anthropic.claude-3-5-sonnet-20241022-v2:0` (Best)
- `anthropic.claude-3-sonnet-20240229-v1:0`

Requirements:
- AWS credentials with Bedrock access
- Model access enabled in AWS console

#### Anthropic API

Requirements:
- API key from https://console.anthropic.com
- Model: `claude-3-5-sonnet-20241022`

### GitHub Configuration

For **private repositories**, generate a Personal Access Token:

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Generate new token with `repo` scope
3. Enter token in the app sidebar

### Advanced Settings

Edit `src/rag_pipeline.py` to customize:

```python
# Embedding dimension
EMBEDDING_DIM = 384

# Retrieval settings
TOP_K = 10

# Chunk size
CHUNK_SIZE = 2000
```

---

## 🧪 Testing

### Test with Sample Code

Create a test repository with sample SQL:

**File: `create_summary.sql`**
```sql
CREATE TABLE CUSTOMER_SUMMARY AS (
  SELECT 
    c.CUSTOMER_ID,
    c.CUSTOMER_NAME,
    SUM(t.AMOUNT) AS TOTAL_PURCHASES
  FROM CUSTOMER_MASTER c
  LEFT JOIN TRANSACTIONS t 
    ON c.CUSTOMER_ID = t.CUSTOMER_ID
  WHERE t.TRANSACTION_DATE >= CURRENT_DATE - 365
  GROUP BY c.CUSTOMER_ID, c.CUSTOMER_NAME
);
```

Query:
- **Table**: CUSTOMER_SUMMARY
- **Column**: TOTAL_PURCHASES

Expected: Traces back to `TRANSACTIONS.AMOUNT` with SUM aggregation.

---

## 🐛 Troubleshooting

### Issue: "Repository not indexed"

**Solution**: Click "Index Repository" in sidebar first.

### Issue: "No lineage found"

**Possible causes**:
- Column name typo (check case sensitivity)
- Code not in indexed files
- Table created outside repository

**Try**:
- Search with different case (e.g., `Total_Purchases` vs `TOTAL_PURCHASES`)
- Check if table exists in Statistics section
- Verify branch is correct

### Issue: "LLM not available"

**Solution**: 
- AWS Bedrock: Check credentials and region
- Anthropic API: Verify API key
- Install: `pip install boto3` or `pip install anthropic`

### Issue: "FAISS not available"

**Solution**: 
```bash
pip install faiss-cpu
# OR for GPU:
pip install faiss-gpu
```

App will fall back to simple similarity search if FAISS unavailable.

### Issue: Git clone fails

**Solution**:
- For private repos, provide GitHub token
- Check network connectivity
- Verify repository URL is correct

---

## 🔒 Security Best Practices

1. **Never commit credentials** to version control
2. Use **environment variables** for API keys
3. For production:
   - Use AWS Secrets Manager
   - Implement role-based access control
   - Rotate API keys regularly
4. **Private repos**: Use fine-grained GitHub tokens with minimal scope

---

## 📊 Performance Tips

### For Large Repositories (1000+ files)

1. **Use FAISS**: Significantly faster than simple search
   ```bash
   pip install faiss-cpu
   ```

2. **Increase chunk size**: Edit `rag_pipeline.py`
   ```python
   CHUNK_SIZE = 3000  # Default: 2000
   ```

3. **Limit file types**: Only index relevant files
   ```python
   extensions = ['.sql', '.bteq']  # Skip .ksh if not needed
   ```

4. **Use SageMaker**: Better performance than local machines

---

## 🎓 How It Works

### 1. Code Ingestion

- Clones GitHub repository
- Scans for `.sql`, `.bteq`, `.ksh` files
- Extracts SQL statements (even from shell scripts)

### 2. Parsing & Chunking

- Parses Teradata-specific syntax
- Identifies tables, columns, joins
- Creates semantic chunks for indexing

### 3. Vector Embedding

- Converts code chunks to embeddings
- Uses TF-IDF or custom embeddings
- Stores in FAISS vector database

### 4. Retrieval (RAG)

When user queries a column:
1. Semantic search finds relevant code
2. Retrieves top-k most relevant chunks
3. Includes file paths and metadata

### 5. LLM Analysis

Claude 3.5 Sonnet:
- Understands SQL semantics
- Traces data transformations
- Identifies source tables
- Builds lineage chain

### 6. Visualization

- Generates interactive graphs
- Shows transformation logic
- Links to source files

---

## 🚢 Deployment

### SageMaker Studio

Already set up! Just run `streamlit run app.py`

### SageMaker Endpoint (Production)

1. Package as Docker container
2. Use SageMaker Hosting
3. Configure autoscaling

### EC2 / ECS

Use the included `Dockerfile` (create one):

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t teradata-lineage .
docker run -p 8501:8501 teradata-lineage
```

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Support for more file types (Python, Spark SQL)
- [ ] Export lineage to CSV/Excel
- [ ] Integration with data catalogs (Alation, Collibra)
- [ ] Real-time lineage tracking
- [ ] Column-level impact analysis
- [ ] Support for other databases (Oracle, SQL Server)

---

## 📝 License

MIT License - see LICENSE file

---

## 🙋 Support

- **Issues**: Open a GitHub issue
- **Questions**: Create a discussion
- **Enterprise**: Contact support@yourcompany.com

---

## 🎉 Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Powered by [Claude 3.5 Sonnet](https://anthropic.com)
- Vector search by [FAISS](https://github.com/facebookresearch/faiss)

---

## 📈 Roadmap

### Q1 2024
- [ ] Add export to data lineage tools
- [ ] Support for complex BTEQ scripts
- [ ] Performance optimization for 10,000+ file repos

### Q2 2024
- [ ] Column-level impact analysis
- [ ] Integration with Airflow DAGs
- [ ] Multi-repository support

### Q3 2024
- [ ] Real-time lineage updates via webhooks
- [ ] Automated lineage documentation generation
- [ ] Support for non-Teradata databases

---

**Happy Lineage Tracing! 🚀**