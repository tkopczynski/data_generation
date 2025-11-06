# Web Interface Guide

## Overview

The Gradio-based web interface provides an intuitive, mobile-responsive way to generate synthetic datasets without using the command line. Perfect for non-technical users or quick data generation tasks.

## Features

✅ **Natural Language Interface** - Describe data in plain English
✅ **Schema Preview** - See the generated YAML schema before creating data
✅ **Advanced YAML Editor** - Full control for power users
✅ **Mobile Responsive** - Works seamlessly on phones and tablets
✅ **File Download** - Download generated CSV files directly from the browser
✅ **Built-in Examples** - Learn from example requests
✅ **Real-time Progress** - See generation status in real-time

## Quick Start

### 1. Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate  # On Windows

# Install with Gradio support
uv pip install -e ".[dev]"
```

### 2. Set OpenAI API Key

```bash
# Create .env file if it doesn't exist
cp .env.example .env

# Add your OpenAI API key to .env
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### 3. Launch the Web Interface

```bash
# Option 1: Using the installed command
data-generation-web

# Option 2: Using Python module
python -m data_generation.web.app

# Option 3: Direct execution
python src/data_generation/web/app.py
```

The interface will be available at:
- **Local**: http://localhost:7860
- **Network**: http://0.0.0.0:7860 (accessible from other devices on your network)

## Usage

### Tab 1: Natural Language (Simple Mode)

Perfect for quick data generation without writing YAML schemas.

**Examples:**
```
Generate 100 users with name, email, and age between 18-80

Create 500 products with product name, price between $10-$1000,
and category (electronics, clothing, food)

Generate 50 users, then 200 transactions with user_id referencing the users

Create 1000 customers with 10% null emails and 5% duplicate names
```

**Steps:**
1. Enter your data request in plain English
2. Click "🚀 Generate Data"
3. Wait for processing (progress bar shows status)
4. Download the generated CSV file

### Tab 2: Schema Preview

Preview the AI-generated YAML schema before creating data.

**Steps:**
1. Describe your data
2. Click "🔍 Preview Schema"
3. Review the YAML schema
4. Copy to Advanced tab if you want to modify it

### Tab 3: Advanced (YAML Schema)

For users who want full control over the schema definition.

**Steps:**
1. Write or paste your YAML schema
2. Set number of rows
3. Specify output filename
4. Click "🚀 Generate Data"

**Example Schema:**
```yaml
- name: user_id
  type: uuid

- name: email
  type: email
  config:
    quality_config:
      null_rate: 0.1        # 10% null values
      duplicate_rate: 0.05  # 5% duplicates

- name: age
  type: int
  config:
    min: 18
    max: 80

- name: status
  type: category
  config:
    categories: [active, inactive, pending]
```

### Tab 4: Help

Built-in documentation with:
- Supported data types
- YAML schema examples
- Quality configuration options
- Foreign key relationships

## Mobile Access

The Gradio interface is fully responsive and works on:
- 📱 Smartphones (iOS/Android)
- 📲 Tablets
- 💻 Desktop browsers

### Accessing from Mobile

1. **Same Network**:
   - Find your computer's IP address: `ip addr` or `ifconfig`
   - On mobile, navigate to: `http://YOUR_IP:7860`

2. **Public Sharing** (temporary):
   Edit `src/data_generation/web/app.py` and change:
   ```python
   app.launch(share=True)  # Creates a public link
   ```
   This creates a temporary public URL (expires in 72 hours).

## Deployment Options

### Option 1: Hugging Face Spaces (Free)

1. Create account at [huggingface.co](https://huggingface.co)
2. Create new Space with Gradio SDK
3. Upload your code
4. Add `OPENAI_API_KEY` to Space secrets
5. Your app is live at: `https://huggingface.co/spaces/USERNAME/SPACE_NAME`

### Option 2: Gradio Cloud

```bash
# Install Gradio CLI
pip install gradio

# Deploy (requires Gradio account)
gradio deploy src/data_generation/web/app.py
```

### Option 3: Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install -e ".[dev]"

ENV OPENAI_API_KEY=""

CMD ["python", "-m", "data_generation.web.app"]
```

```bash
# Build and run
docker build -t data-generation-web .
docker run -p 7860:7860 -e OPENAI_API_KEY=your-key data-generation-web
```

### Option 4: Cloud Platforms

Deploy to any platform that supports Python web apps:
- **Railway**: Connect GitHub repo, auto-deploy
- **Render**: Web service with Dockerfile
- **Fly.io**: `fly launch` and `fly deploy`
- **Google Cloud Run**: Container-based deployment
- **AWS App Runner**: Direct from GitHub

## Configuration

### Port and Host

Edit `src/data_generation/web/app.py`:

```python
app.launch(
    server_name="0.0.0.0",  # Allow external connections
    server_port=7860,       # Change port if needed
    share=False,            # Set True for public link
)
```

### Styling

Gradio themes can be customized:

```python
with gr.Blocks(
    theme=gr.themes.Soft(),  # Options: Default, Soft, Glass, Monochrome
    css=custom_css
) as app:
```

## Troubleshooting

### "OPENAI_API_KEY not found"

**Solution**:
```bash
# Check .env file exists
cat .env

# Ensure it contains:
OPENAI_API_KEY=sk-...

# Restart the application
```

### "Address already in use"

**Solution**:
```bash
# Kill process on port 7860
lsof -ti:7860 | xargs kill -9

# Or change port in app.py
```

### "Module not found: gradio"

**Solution**:
```bash
# Reinstall dependencies
uv pip install -e ".[dev]"
```

### File not found after generation

**Issue**: Generated files may be in working directory instead of expected location.

**Solution**: Check the file path in the status message. Files are saved with absolute paths.

## Features Roadmap

Future enhancements:
- [ ] Data visualization (charts/stats)
- [ ] Multi-file download (ZIP)
- [ ] Schema library (save/load templates)
- [ ] Data preview before download
- [ ] Batch generation (multiple datasets at once)
- [ ] Authentication for multi-user deployments
- [ ] File upload for reference tables

## Support

- **Documentation**: See main [README.md](README.md) and [CLAUDE.md](CLAUDE.md)
- **Issues**: Report bugs on GitHub
- **Examples**: Check `/examples` directory

## CLI vs Web Interface

| Feature | CLI | Web |
|---------|-----|-----|
| Installation | Python package | Same + Gradio |
| Interface | Terminal commands | Web browser |
| Mobile support | No | Yes |
| Sharing with non-technical users | Difficult | Easy |
| Automation/scripting | Excellent | Limited |
| Visual feedback | Text only | Rich UI + progress bars |
| File download | Local filesystem | Browser download |

**When to use CLI**: Automation, scripting, CI/CD pipelines, power users

**When to use Web**: Demos, non-technical users, mobile access, quick generation
