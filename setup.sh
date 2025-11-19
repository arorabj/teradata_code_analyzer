#!/bin/bash

# Teradata Lineage RAG - Setup Script
# This script sets up the environment for running the application

set -e  # Exit on error

echo "🚀 Setting up Teradata Lineage RAG System..."
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.9 or higher is required (found: $python_version)"
    exit 1
fi
echo "✅ Python version: $python_version"
echo ""

# Check Git
echo "📋 Checking Git installation..."
if ! command -v git &> /dev/null; then
    echo "❌ Error: Git is not installed"
    echo "   Please install Git first: https://git-scm.com/downloads"
    exit 1
fi
echo "✅ Git is installed"
echo ""

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists"
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet
echo "✅ Pip upgraded"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

# Create src directory structure
echo "📁 Creating project structure..."
mkdir -p src
touch src/__init__.py

# Check if module files exist
if [ ! -f "src/github_ingestion.py" ]; then
    echo "⚠️  Warning: src/github_ingestion.py not found"
    echo "   Please copy all module files to the src/ directory"
fi
echo "✅ Project structure ready"
echo ""

# Check for AWS credentials (optional)
echo "🔐 Checking AWS credentials..."
if [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$AWS_PROFILE" ]; then
    echo "⚠️  Warning: No AWS credentials found"
    echo "   If using AWS Bedrock, set AWS credentials:"
    echo "   export AWS_ACCESS_KEY_ID=your_key"
    echo "   export AWS_SECRET_ACCESS_KEY=your_secret"
    echo "   export AWS_DEFAULT_REGION=us-east-1"
else
    echo "✅ AWS credentials configured"
fi
echo ""

# Check for Anthropic API key (optional)
echo "🔐 Checking Anthropic API key..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: No Anthropic API key found"
    echo "   If using Anthropic API, set:"
    echo "   export ANTHROPIC_API_KEY=your_api_key"
else
    echo "✅ Anthropic API key configured"
fi
echo ""

# Success message
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Ensure all module files are in the src/ directory:"
echo "      - github_ingestion.py"
echo "      - code_parser.py"
echo "      - rag_pipeline.py"
echo "      - lineage_analyzer.py"
echo "      - visualizer.py"
echo ""
echo "   2. Configure your LLM credentials (AWS or Anthropic)"
echo ""
echo "   3. Run the application:"
echo "      streamlit run app.py"
echo ""
echo "   4. Open your browser to the displayed URL"
echo ""
echo "🎉 Happy lineage tracing!"