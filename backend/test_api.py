import asyncio
from httpx import AsyncClient
import json

async def main():
    async with AsyncClient(base_url="http://localhost:8000/api/v1") as client:
        login_res = await client.post("/auth/login", json={"username": "superadmin", "password": "password123"})
        if login_res.status_code != 200:
            login_res = await client.post("/auth/login", json={"username": "user1", "password": "password123"})
            
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("--- Testing Chat Stream ---")
        async with client.stream("POST", "/chat/stream", json={"query": "Salom, qisqacha javob ber"}, headers=headers) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    dataStr = line[6:]
                    if dataStr == "[DONE]":
                        continue
                    data = json.loads(dataStr)
                    if data.get("type") in ["provider_start", "usage", "all_failed", "error"]:
                        print(data)
                    elif data.get("type") == "token":
                        print(data["content"], end="", flush=True)
            print()
            
        print("--- Testing Admin LLM Usage ---")
        login_res = await client.post("/auth/login", json={"username": "superadmin", "password": "password123"})
        if login_res.status_code == 200:
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            usage_res = await client.get("/admin/usage", headers=headers)
            print("Usage:", json.dumps(usage_res.json(), indent=2))
            
            status_res = await client.get("/admin/providers/status", headers=headers)
            print("Status:", json.dumps(status_res.json(), indent=2))
        
if __name__ == "__main__":
    asyncio.run(main())
