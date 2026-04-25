import os
import uvicorn
from dotenv import load_dotenv

# Load .env from the root
load_dotenv()

if __name__ == "__main__":
    # Add src and services/api to PYTHONPATH
    root = os.getcwd()
    os.environ["PYTHONPATH"] = f"{root};{os.path.join(root, 'src')};{os.path.join(root, 'services', 'api')}"
    
    uvicorn.run(
        "services.api.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
