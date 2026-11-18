CUSTOMER = {"name": "Arun", "email": "arun@example.com", "phone": "9876543210"}


def create(client, auth, data=CUSTOMER):
    return client.post("/customers", json=data, headers=auth)


# ---------- happy paths ----------
def test_create_customer(client, auth):
    r = create(client, auth)
    assert r.status_code == 201
    assert r.json()["email"] == "arun@example.com"
    assert "id" in r.json()


def test_list_customers(client, auth):
    create(client, auth)
    r = client.get("/customers", headers=auth)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_customer(client, auth):
    cid = create(client, auth).json()["id"]
    r = client.get(f"/customers/{cid}", headers=auth)
    assert r.status_code == 200
    assert r.json()["name"] == "Arun"


def test_update_customer(client, auth):
    cid = create(client, auth).json()["id"]
    new = {"name": "Arun K", "email": "arun@example.com", "phone": "111"}
    r = client.put(f"/customers/{cid}", json=new, headers=auth)
    assert r.status_code == 200
    assert r.json()["name"] == "Arun K"


def test_delete_customer(client, auth):
    cid = create(client, auth).json()["id"]
    assert client.delete(f"/customers/{cid}", headers=auth).status_code == 204
    assert client.get(f"/customers/{cid}", headers=auth).status_code == 404


# ---------- 401 ----------
def test_missing_api_key_401(client):
    assert client.get("/customers").status_code == 401


def test_wrong_api_key_401(client):
    r = client.get("/customers", headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


# ---------- 404 ----------
def test_get_missing_404(client, auth):
    assert client.get("/customers/999", headers=auth).status_code == 404


def test_update_missing_404(client, auth):
    r = client.put("/customers/999", json=CUSTOMER, headers=auth)
    assert r.status_code == 404


def test_delete_missing_404(client, auth):
    assert client.delete("/customers/999", headers=auth).status_code == 404


# ---------- 409 ----------
def test_duplicate_email_409(client, auth):
    create(client, auth)
    assert create(client, auth).status_code == 409


def test_update_to_existing_email_409(client, auth):
    create(client, auth)
    other = create(client, auth, {"name": "B", "email": "b@example.com"}).json()
    r = client.put(f"/customers/{other['id']}", json=CUSTOMER, headers=auth)
    assert r.status_code == 409


# ---------- 422 ----------
def test_invalid_email_422(client, auth):
    r = create(client, auth, {"name": "X", "email": "not-an-email"})
    assert r.status_code == 422


def test_missing_name_422(client, auth):
    r = create(client, auth, {"email": "x@example.com"})
    assert r.status_code == 422


def test_bad_id_type_422(client, auth):
    assert client.get("/customers/abc", headers=auth).status_code == 422