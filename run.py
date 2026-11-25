import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\n  Nihongo Arena running at http://localhost:{port}\n")
    uvicorn.run("server.main:app", host="0.0.0.0", port=port)
