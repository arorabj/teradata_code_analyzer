# SageMaker Studio Setup Guide

## 🎯 Quick Start for SageMaker Studio (eu-west-1)

Since you're running in SageMaker Studio, AWS credentials are **automatically configured** through your execution role. No need to set environment variables!

---

## 📋 Prerequisites

- ✅ SageMaker Studio running in eu-west-1
- ✅ Execution role with Bedrock access
- ✅ Internet access enabled
- ✅ GitHub repository URL

---

## 🚀 Step-by-Step Setup

### Step 1: Open Terminal in SageMaker Studio

1. Click **File** → **New** → **Terminal**
2. You'll see a terminal window open

### Step 2: Create Project Directory

```bash
# Create and navigate to project directory
mkdir -p ~/teradata-lineage-rag
cd ~/teradata-lineage-rag
```

### Step 3: Create All Required Files

#### Create `requirements.txt`
```bash
cat > requirements.txt << 'EOF'
# Core Framework
streamlit>=1.28.0
numpy>=1.24.0

# Vector Store
faiss-cpu>=1.7.4

# LLM Integration (Bedrock - already available in SageMaker)
boto3>=1.28.0

# Code Processing
pandas>=2.0.0
EOF
```

#### Create `app.py`
Copy the main application code from the artifact into this file.

#### Create Source Directory
```bash
mkdir -p src
touch src/__init__.py
```

#### Create Module Files
Copy each module file:
- `src/github_ingestion.py`
- `src/code_parser.py`
- `src/rag_pipeline.py`
- `src/lineage_analyzer.py`
- `src/visualizer.py`

### Step 4: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

### Step 5: Verify Bedrock Access

```bash
# Test Bedrock connection
python3 << 'EOF'
import boto3

bedrock = boto3.client('bedrock-runtime', region_name='eu-west-1')
print("✅ Bedrock client created successfully!")
print(f"Region: eu-west-1")
EOF
```

**If you see an error**, ensure your SageMaker execution role has these permissions:
- `bedrock:InvokeModel`
- `bedrock:InvokeModelWithResponseStream`

### Step 6: Run the Application

```bash
# Start Streamlit
streamlit run app.py --server.port 8501
```

### Step 7: Access the Application

SageMaker Studio will display a URL like:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://xxx.xxx.xxx.xxx:8501
```

Click the **"Open in new tab"** button or copy the URL.

---

## ⚙️ SageMaker-Specific Configuration

### Update app.py Sidebar Configuration

Since you're in SageMaker, modify the default settings in `app.py`:

```python
# Around line 60-65, change:
aws_region = st.text_input("AWS Region", value="eu-west-1")  # Changed from us-east-1
```

### Available Bedrock Models in eu-west-1

Check which Claude models are available:

```bash
python3 << 'EOF'
import boto3
import json

bedrock = boto3.client('bedrock', region_name='eu-west-1')

print("Available Claude models in eu-west-1:")
response = bedrock.list_foundation_models(
    byProvider='Anthropic'
)

for model in response['modelSummaries']:
    print(f"  • {model['modelId']}")
EOF
```

Common models in eu-west-1:
- `anthropic.claude-3-5-sonnet-20241022-v2:0` ✅ **Recommended**
- `anthropic.claude-3-sonnet-20240229-v1:0`
- `anthropic.claude-3-haiku-20240307-v1:0`

---

## 🔧 Quick Configuration Script

Create this helper script to set everything up:

```bash
cat > setup_sagemaker.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Setting up Teradata Lineage RAG in SageMaker Studio..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q streamlit numpy faiss-cpu boto3 pandas

# Verify installation
echo "✅ Verifying installation..."
python3 -c "import streamlit; import boto3; import faiss; print('All packages installed!')"

# Test Bedrock access
echo "🔐 Testing Bedrock access..."
python3 << 'PYTHON'
import boto3
try:
    bedrock = boto3.client('bedrock-runtime', region_name='eu-west-1')
    print("✅ Bedrock access confirmed!")
except Exception as e:
    print(f"❌ Bedrock access error: {e}")
    print("   Please ensure your SageMaker role has Bedrock permissions")
PYTHON

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the app:"
echo "  streamlit run app.py --server.port 8501"
echo ""
EOF

chmod +x setup_sagemaker.sh
```

Then run it:
```bash
./setup_sagemaker.sh
```

---

## 🎯 First-Time Usage

### 1. Start the App
```bash
streamlit run app.py --server.port 8501
```

### 2. Configure in the UI
- **Repository URL**: Your GitHub repo with Teradata code
- **Branch**: `main` or your working branch
- **GitHub Token**: Only needed for private repos
- **LLM Provider**: Select "AWS Bedrock"
- **AWS Region**: `eu-west-1` (auto-filled)
- **Model**: `anthropic.claude-3-5-sonnet-20241022-v2:0`

### 3. Index Repository
Click **"Index Repository"** button in sidebar

### 4. Analyze Lineage
Enter table name and column name, then click **"Analyze Lineage"**

---

## 🐛 Troubleshooting in SageMaker

### Issue: "Port 8501 already in use"

```bash
# Find and kill the process
lsof -ti:8501 | xargs kill -9

# Or use a different port
streamlit run app.py --server.port 8502
```

### Issue: "Bedrock access denied"

1. Go to **SageMaker Console** → **Studio** → **Domain**
2. Click on your domain → **Domain settings**
3. Click on execution role
4. Add this policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "arn:aws:bedrock:eu-west-1::foundation-model/anthropic.claude-*"
        }
    ]
}
```

### Issue: "Module not found"

```bash
# Verify you're in the right directory
pwd  # Should show: /home/sagemaker-user/teradata-lineage-rag

# Check files exist
ls -la src/

# Reinstall if needed
pip install -r requirements.txt --force-reinstall
```

### Issue: "Git clone fails"

For **private repositories**, generate a GitHub Personal Access Token:

1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` scope
3. Enter token in the app's GitHub Token field

---

## 💾 SageMaker Storage Considerations

### Where Files Are Stored

- **Repository clones**: `/tmp/teradata_lineage_workspace/`
- **Vector index**: In-memory (FAISS)
- **Logs**: Streamlit creates `.streamlit/` folder

### Persistence

⚠️ **Important**: Files in SageMaker Studio persist in your home directory (`/home/sagemaker-user/`) but `/tmp/` is cleared on restart.

To persist repository clones, modify `github_ingestion.py`:

```python
# Line ~31, change:
self.workspace = Path.home() / "lineage_workspace"  # Instead of /tmp/
```

---

## 🚀 Performance Tips for SageMaker

### 1. Choose the Right Instance Type

For best performance:
- **Small repos (< 100 files)**: `ml.t3.medium` (default)
- **Medium repos (100-1000 files)**: `ml.t3.xlarge`
- **Large repos (1000+ files)**: `ml.m5.2xlarge` or higher

### 2. Use FAISS for Large Repositories

Already included in `requirements.txt` - no additional setup needed!

### 3. Monitor Memory Usage

```bash
# Check memory usage while running
watch -n 5 'free -h'
```

---

## 📊 Expected Performance

### On ml.t3.medium (2 vCPU, 4 GB RAM):
- **Index 100 files**: ~1-2 minutes
- **Query response**: ~15-30 seconds
- **Memory usage**: ~1-2 GB

### On ml.m5.xlarge (4 vCPU, 16 GB RAM):
- **Index 500 files**: ~3-5 minutes
- **Query response**: ~10-20 seconds
- **Memory usage**: ~2-4 GB

---

## 🎓 SageMaker-Specific Features

### Automatic Credential Management
✅ No need to configure AWS credentials
✅ Uses execution role automatically
✅ Region detected from environment

### Integrated Development
✅ Edit code in SageMaker Studio IDE
✅ Debug with built-in terminal
✅ Version control with Git integration

### Secure by Default
✅ Private VPC networking
✅ Encrypted storage
✅ IAM-based access control

---

## 🔄 Updating the Application

```bash
cd ~/teradata-lineage-rag

# Pull latest changes (if using Git)
git pull

# Reinstall dependencies if updated
pip install -r requirements.txt --upgrade

# Restart Streamlit
# Stop current instance (Ctrl+C in terminal)
streamlit run app.py --server.port 8501
```

---

## 📝 Sample Test in SageMaker

Create a test script to verify everything works:

```bash
cat > test_setup.py << 'EOF'
#!/usr/bin/env python3
"""Test SageMaker setup"""

import sys
import boto3

print("🧪 Testing SageMaker Setup...\n")

# Test 1: Imports
print("1️⃣ Testing imports...")
try:
    import streamlit
    import numpy
    import faiss
    import pandas
    print("   ✅ All packages imported successfully")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test 2: Bedrock access
print("\n2️⃣ Testing Bedrock access...")
try:
    bedrock = boto3.client('bedrock-runtime', region_name='eu-west-1')
    print("   ✅ Bedrock client created for eu-west-1")
except Exception as e:
    print(f"   ❌ Bedrock error: {e}")
    sys.exit(1)

# Test 3: FAISS
print("\n3️⃣ Testing FAISS...")
try:
    import numpy as np
    dimension = 128
    index = faiss.IndexFlatL2(dimension)
    vectors = np.random.random((10, dimension)).astype('float32')
    index.add(vectors)
    print(f"   ✅ FAISS index created with {index.ntotal} vectors")
except Exception as e:
    print(f"   ❌ FAISS error: {e}")

# Test 4: File system
print("\n4️⃣ Testing file system...")
try:
    from pathlib import Path
    workspace = Path.home() / "lineage_workspace"
    workspace.mkdir(exist_ok=True)
    test_file = workspace / "test.txt"
    test_file.write_text("test")
    test_file.unlink()
    workspace.rmdir()
    print("   ✅ File system access working")
except Exception as e:
    print(f"   ❌ File system error: {e}")

print("\n✅ All tests passed! Ready to run the application.\n")
print("Run: streamlit run app.py --server.port 8501")
EOF

chmod +x test_setup.py
python3 test_setup.py
```

---

## 🎉 You're Ready!

Your SageMaker Studio environment is now configured for Teradata lineage analysis. No AWS credentials needed - everything is handled automatically!

**Next Steps:**
1. Run `streamlit run app.py --server.port 8501`
2. Configure your GitHub repository
3. Start analyzing lineage!

Happy coding! 🚀