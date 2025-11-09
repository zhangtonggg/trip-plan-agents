# trip-plan-agents
## Prepare
**1.Clone the Git repository**
```bash
git clone <REPO-URL> trip-plan-agents
```
**2.Configure the .env file**

Follow these steps to set up environment variables :
```bash
# Navigate to the project directory
cd trip-plan-agents 

# Copy the template file to create a usable .env file
cp .env.example .env  

# Edit the .env file:
AMAP_API_KEY=your_amap_key_here
QWEN_API_KEY=your_qwen_key_here
```

## Run the Project
```bash
# Navigate to the project directory
cd trip-plan-agents 

# Create a virtual environment
pip install uv
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Start the application
python -m src.agent
```