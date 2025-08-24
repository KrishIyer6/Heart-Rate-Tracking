def test_register_and_login(client):
    # Register
    res = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "Test1234"
    })
    assert res.status_code == 201

    # Login
    res = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "Test1234"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "access_token" in data
