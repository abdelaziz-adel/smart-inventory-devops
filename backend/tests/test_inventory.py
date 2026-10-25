import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app, Base, get_db

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine)

@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    def override():
        with TestingSession() as db:
            yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_product_lifecycle(client):
    payload = {"name": "Keyboard", "quantity": 3, "min_stock": 5, "price": 100.0}
    created = client.post("/products", json=payload)
    assert created.status_code == 201
    product_id = created.json()["id"]
    assert len(client.get("/products/low-stock").json()) == 1
    assert client.get("/reports/summary").json()["low_stock_products"] == 1
    assert "Keyboard" in client.get("/reports/inventory.csv").text
    payload["quantity"] = 10
    assert client.put(f"/products/{product_id}", json=payload).status_code == 200
    assert client.get("/products/low-stock").json() == []
    assert client.delete(f"/products/{product_id}").status_code == 204
    assert client.get("/products").json() == []

def test_negative_stock_rejected(client):
    bad = {"name": "Pen", "quantity": -1, "min_stock": 5, "price": 1}
    assert client.post("/products", json=bad).status_code == 422
