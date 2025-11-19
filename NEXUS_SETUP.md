# Internal Nexus Repository Setup

## 🔧 Configuring pip for Internal Nexus Repository

Since you're using an internal Nexus repository, you need to configure pip to use it instead of PyPI.

---

## 🚀 Quick Setup Options

### Option 1: Using pip.conf (Recommended for SageMaker)

Create a pip configuration file in your SageMaker environment:

```bash
# Create pip config directory
mkdir -p ~/.config/pip

# Create pip.conf file
cat > ~/.config/pip/pip.conf << 'EOF'
[global]
index-url = https://your-nexus-repo.company.com/repository/pypi-group/simple
trusted-host = your-nexus-repo.company.com
timeout = 60

[install]
trusted-host = your-nexus-repo.company.com
EOF
```

**Replace** `your-nexus-repo.company.com` with your actual Nexus URL.

#### With Authentication:

If your Nexus requires authentication:

```bash
cat > ~/.config/pip/pip.conf << 'EOF'
[global]
index-url = https://username:password@your-nexus-repo.company.com/repository/pypi-group/simple
trusted-host = your-nexus-repo.company.com
timeout = 60

[install]
trusted-host = your-nexus-repo.company.com
EOF
```

**⚠️ Security Note**: For production, use a token instead of password.

---

### Option 2: Using Environment Variables

Set environment variables in your terminal:

```bash
# Add to ~/.bashrc for persistence
cat >> ~/.bashrc << 'EOF'

# Nexus Pip Configuration
export PIP_INDEX_URL=https://your-nexus-repo.company.com/repository/pypi-group/simple
export PIP_TRUSTED_HOST=your-nexus-repo.company.com
EOF

# Apply changes
source ~/.bashrc
```

---

### Option 3: Command Line (Per Installation)

Use pip with inline configuration:

```bash
# Install with custom index
pip install --index-url https://your-nexus-repo.company.com/repository/pypi-group/simple \
            --trusted-host your-nexus-repo.company.com \
            streamlit numpy faiss-cpu boto3 pandas

# Or install from requirements.txt
pip install -r requirements.txt \
            --index-url https://your-nexus-repo.company.com/repository/pypi-group/simple \
            --trusted-host your-nexus-repo.company.com
```

---

## 🔐 Authentication Methods

### Method 1: Inline Credentials

```bash
pip install --index-url https://username:password@your-nexus-repo.company.com/repository/pypi-group/simple \
            --trusted-host your-nexus-repo.company.com \
            streamlit
```

### Method 2: Using .netrc File (More Secure)

Create `~/.netrc` file:

```bash
cat > ~/.netrc << 'EOF'
machine your-nexus-repo.company.com
login your-username
password your-password
EOF

chmod 600 ~/.netrc
```

Then use pip without credentials in URL:

```bash
pip install --index-url https://your-nexus-repo.company.com/repository/pypi-group/simple \
            --trusted-host your-nexus-repo.company.com \
            streamlit
```

### Method 3: Using Nexus Token (Recommended)

Generate a token in Nexus, then:

```bash
cat > ~/.config/pip/pip.conf << 'EOF'
[global]
index-url = https://token:YOUR_NEXUS_TOKEN@your-nexus-repo.company.com/repository/pypi-group/simple
trusted-host = your-nexus-repo.company.com
EOF
```

---

## 📦 Updated requirements.txt for Nexus

Your `requirements.txt` remains the same:

```text
# Core Framework
streamlit>=1.28.0
numpy>=1.24.0

# Vector Store
faiss-cpu>=1.7.4

# LLM Integration
boto3>=1.28.0

# Code Processing
pandas>=2.0.0
```

But install using:

```bash
pip install -r requirements.txt
```

pip will automatically use your configured Nexus repository.

---

## 🧪 Testing Nexus Configuration

### Test 1: Verify pip configuration

```bash
pip config list
```

Expected output:
```
global.index-url='https://your-nexus-repo.company.com/repository/pypi-group/simple'
global.trusted-host='your-nexus-repo.company.com'
```

### Test 2: Search for a package

```bash
pip search streamlit --index-url https://your-nexus-repo.company.com/repository/pypi-group/simple
```

### Test 3: Install a single package

```bash
pip install numpy --trusted-host your-nexus-repo.company.com
```

---

## 🚀 Complete SageMaker Setup Script with Nexus

Create this setup script:

```bash
cat > setup_with_nexus.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Setting up Teradata Lineage RAG with Nexus repository..."
echo ""

# Configuration - UPDATE THESE VALUES
NEXUS_URL="your-nexus-repo.company.com"
NEXUS_REPO="pypi-group"
NEXUS_USERNAME="your-username"  # Optional
NEXUS_PASSWORD="your-password"  # Optional

echo "📝 Configuring pip for Nexus..."

# Create pip config directory
mkdir -p ~/.config/pip

# Create pip.conf
if [ -n "$NEXUS_USERNAME" ] && [ -n "$NEXUS_PASSWORD" ]; then
    # With authentication
    cat > ~/.config/pip/pip.conf << PIPCONF
[global]
index-url = https://${NEXUS_USERNAME}:${NEXUS_PASSWORD}@${NEXUS_URL}/repository/${NEXUS_REPO}/simple
trusted-host = ${NEXUS_URL}
timeout = 60

[install]
trusted-host = ${NEXUS_URL}
PIPCONF
    echo "✅ pip configured with authentication"
else
    # Without authentication
    cat > ~/.config/pip/pip.conf << PIPCONF
[global]
index-url = https://${NEXUS_URL}/repository/${NEXUS_REPO}/simple
trusted-host = ${NEXUS_URL}
timeout = 60

[install]
trusted-host = ${NEXUS_URL}
PIPCONF
    echo "✅ pip configured without authentication"
fi

echo ""
echo "🧪 Testing Nexus connection..."
pip config list

echo ""
echo "📦 Installing dependencies from Nexus..."
pip install -q streamlit numpy faiss-cpu boto3 pandas

echo ""
echo "✅ Verifying installation..."
python3 << 'PYTHON'
import sys
try:
    import streamlit
    import numpy
    import faiss
    import boto3
    import pandas
    print("✅ All packages installed successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
PYTHON

echo ""
echo "🔐 Testing Bedrock access..."
python3 << 'PYTHON'
import boto3
try:
    bedrock = boto3.client('bedrock-runtime', region_name='eu-west-1')
    print("✅ Bedrock access confirmed!")
except Exception as e:
    print(f"❌ Bedrock error: {e}")
PYTHON

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Copy all module files to src/ directory"
echo "  2. Run: streamlit run app.py --server.port 8501"
echo ""
EOF

chmod +x setup_with_nexus.sh
```

**Edit the script** to add your Nexus details, then run:

```bash
./setup_with_nexus.sh
```

---

## 🔍 Common Nexus Configurations

### Configuration 1: Simple Nexus (No Auth)

```ini
[global]
index-url = https://nexus.company.com/repository/pypi-group/simple
trusted-host = nexus.company.com
```

### Configuration 2: Nexus with Basic Auth

```ini
[global]
index-url = https://username:password@nexus.company.com/repository/pypi-group/simple
trusted-host = nexus.company.com
```

### Configuration 3: Nexus with Token

```ini
[global]
index-url = https://token:abc123xyz@nexus.company.com/repository/pypi-group/simple
trusted-host = nexus.company.com
```

### Configuration 4: Multiple Repositories (Fallback)

```ini
[global]
index-url = https://nexus.company.com/repository/pypi-group/simple
extra-index-url = https://pypi.org/simple
trusted-host = nexus.company.com
```

### Configuration 5: Behind Corporate Proxy

```ini
[global]
index-url = https://nexus.company.com/repository/pypi-group/simple
trusted-host = nexus.company.com
proxy = http://proxy.company.com:8080
```

---

## 🐛 Troubleshooting Nexus Issues

### Issue: "Could not find a version that satisfies the requirement"

**Cause**: Package not in Nexus repository

**Solutions**:

1. **Add fallback to PyPI**:
```bash
pip install streamlit \
    --index-url https://nexus.company.com/repository/pypi-group/simple \
    --extra-index-url https://pypi.org/simple \
    --trusted-host nexus.company.com
```

2. **Ask admin to proxy PyPI** in Nexus

3. **Download and upload** package to Nexus manually

### Issue: "SSL Certificate Verification Failed"

**Solutions**:

1. **Add to trusted hosts**:
```bash
pip install --trusted-host nexus.company.com streamlit
```

2. **Or disable SSL verification** (not recommended for production):
```bash
pip install --index-url https://nexus.company.com/repository/pypi-group/simple \
            --trusted-host nexus.company.com \
            streamlit
```

3. **Install corporate CA certificate**:
```bash
# Copy your company's CA certificate
sudo cp company-ca.crt /etc/ssl/certs/
sudo update-ca-certificates
```

### Issue: "Authentication failed"

**Check**:
1. Username/password correct
2. Token not expired
3. User has read access to repository

**Test authentication**:
```bash
curl -u username:password https://nexus.company.com/repository/pypi-group/simple/
```

### Issue: "Connection timeout"

**Solutions**:
1. Increase timeout in pip.conf:
```ini
[global]
timeout = 120
```

2. Check network connectivity:
```bash
ping nexus.company.com
telnet nexus.company.com 443
```

---

## 📋 Verification Checklist

- [ ] pip.conf created in `~/.config/pip/`
- [ ] Nexus URL is correct
- [ ] Authentication credentials work
- [ ] `pip config list` shows correct settings
- [ ] Can install test package: `pip install requests`
- [ ] All required packages available in Nexus
- [ ] SSL/TLS working or trusted-host set

---

## 🔄 Installing Packages

### Method 1: Using configured pip (Recommended)

```bash
# After pip.conf is set up
pip install -r requirements.txt
```

### Method 2: Explicit command line

```bash
pip install -r requirements.txt \
    --index-url https://nexus.company.com/repository/pypi-group/simple \
    --trusted-host nexus.company.com
```

### Method 3: Individual packages

```bash
pip install streamlit --trusted-host nexus.company.com
pip install numpy --trusted-host nexus.company.com
pip install faiss-cpu --trusted-host nexus.company.com
pip install boto3 --trusted-host nexus.company.com
pip install pandas --trusted-host nexus.company.com
```

---

## 💡 Pro Tips for Nexus + SageMaker

### 1. Persist pip Configuration

Add to SageMaker lifecycle configuration:

```bash
# This runs every time your Studio instance starts
mkdir -p ~/.config/pip
cat > ~/.config/pip/pip.conf << 'EOF'
[global]
index-url = https://nexus.company.com/repository/pypi-group/simple
trusted-host = nexus.company.com
EOF
```

### 2. Cache Packages Locally

```bash
# Download packages to local cache
pip download -r requirements.txt -d /home/sagemaker-user/pip-cache/

# Install from cache
pip install --no-index --find-links=/home/sagemaker-user/pip-cache/ -r requirements.txt
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📞 Getting Help

If you encounter issues:

1. **Check Nexus status** with your admin
2. **Verify credentials** are correct
3. **Test connectivity**: `curl https://nexus.company.com`
4. **Check package availability** in Nexus web UI
5. **Review Nexus logs** (if you have access)

---

## ✅ Final Setup Command

Once pip.conf is configured:

```bash
cd ~/teradata-lineage-rag
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

That's it! Your packages will now install from your internal Nexus repository. 🎉