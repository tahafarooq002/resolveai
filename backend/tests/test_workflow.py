def test_user_registration_and_ticket_creation(client):
    # 1. Register a new user/organization
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User",
            "organization_name": "Test Org"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a support ticket
    ticket_response = client.post(
        "/api/v1/tickets",
        headers=headers,
        json={
            "subject": "Billing Issue",
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "messages": [{"role": "customer", "content": "I was charged twice."}]
        }
    )
    assert ticket_response.status_code == 200
    ticket_data = ticket_response.json()
    assert ticket_data["subject"] == "Billing Issue"
    assert ticket_data["status"] == "open"