import os
import httpx
from fastapi import FastAPI, HTTPException, Response
from prometheus_client import Counter, CONTENT_TYPE_LATEST, generate_latest

app = FastAPI(title="Low Stock Alerts")
INVENTORY_API_URL = os.getenv("INVENTORY_API_URL", "http://backend:8000")
checks = Counter("inventory_alert_checks_total", "Number of low stock queries")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/alerts")
async def alerts():
    checks.inc()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{INVENTORY_API_URL}/products/low-stock")
            response.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(503, "Inventory service unavailable")
    return [{"product_id": p["id"], "product": p["name"],
             "quantity": p["quantity"], "min_stock": p["min_stock"],
             "message": f"Low stock: {p['name']}"} for p in response.json()]
