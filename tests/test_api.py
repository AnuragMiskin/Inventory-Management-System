from fastapi import status


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["message"] == "Welcome to Inventory Management System"
    assert "/docs" in body["detail"]


def test_create_and_list_products(client):
    create_resp = client.post("/products", json={"name": "Apple", "quantity": 10})
    assert create_resp.status_code == status.HTTP_200_OK
    created = create_resp.json()
    assert created["name"] == "Apple"
    assert created["quantity"] == 10
    assert isinstance(created["id"], int)

    list_resp = client.get("/products")
    assert list_resp.status_code == status.HTTP_200_OK
    products = list_resp.json()
    assert len(products) >= 1

    # Ensure created product is present
    assert any(p["name"] == "Apple" and p["quantity"] == 10 for p in products)


def test_update_product_success_and_404(client):
    create_resp = client.post("/products", json={"name": "Banana", "quantity": 5})
    pid = create_resp.json()["id"]

    update_resp = client.put(f"/products/{pid}", json={"quantity": 12})
    assert update_resp.status_code == status.HTTP_200_OK
    updated = update_resp.json()
    assert updated["id"] == pid
    assert updated["quantity"] == 12

    not_found_resp = client.put("/products/999999", json={"quantity": 1})
    assert not_found_resp.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_resp.json()["detail"] == "Product not found"


def test_delete_product_success_and_404(client):
    create_resp = client.post("/products", json={"name": "Orange", "quantity": 3})
    pid = create_resp.json()["id"]

    delete_resp = client.delete(f"/products/{pid}")
    assert delete_resp.status_code == status.HTTP_204_NO_CONTENT
    assert delete_resp.text == ""

    not_found_resp = client.delete("/products/999999")
    assert not_found_resp.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_resp.json()["detail"] == "Product not found"


def test_inventory_add_success_and_404(client):
    # add to missing product
    missing_resp = client.post("/inventory/add", json={"productId": 999999, "quantity": 7})
    assert missing_resp.status_code == status.HTTP_404_NOT_FOUND
    assert missing_resp.json()["detail"] == "Product not found"

    # create then add
    create_resp = client.post("/products", json={"name": "Milk", "quantity": 2})
    pid = create_resp.json()["id"]

    add_resp = client.post("/inventory/add", json={"productId": pid, "quantity": 5})
    assert add_resp.status_code == status.HTTP_200_OK
    updated = add_resp.json()
    assert updated["id"] == pid
    assert updated["quantity"] == 7


def test_inventory_remove_success_insufficient_stock_400_and_404(client):
    # remove from missing product
    missing_resp = client.post(
        "/inventory/remove", json={"productId": 999999, "quantity": 1}
    )
    assert missing_resp.status_code == status.HTTP_404_NOT_FOUND
    assert missing_resp.json()["detail"] == "Product not found"

    # create product with small stock, then remove more than available
    create_resp = client.post("/products", json={"name": "Bread", "quantity": 2})
    pid = create_resp.json()["id"]

    bad_remove = client.post(
        "/inventory/remove", json={"productId": pid, "quantity": 5}
    )
    assert bad_remove.status_code == status.HTTP_400_BAD_REQUEST
    assert bad_remove.json()["detail"] == "insufficient stock"

    # successful remove
    good_remove = client.post(
        "/inventory/remove", json={"productId": pid, "quantity": 2}
    )
    assert good_remove.status_code == status.HTTP_200_OK
    updated = good_remove.json()
    assert updated["quantity"] == 0
