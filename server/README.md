# Running the server

## Setup

### 1. Install uv (if not already installed)

**Windows:**
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Mac/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Add uv to your PATH (if not already in PATH)
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 3. Sync dependencies (this creates the .venv directory)
```bash
uv sync
```

### 4. Activate the virtual environment

**Windows (Git Bash):**
```bash
source .venv/Scripts/activate
```

**Mac/Linux:**
```bash
source .venv/bin/activate
```

### 5. Start the server
```bash
fastapi dev main.py
```