
import pytest
import io
import pandas as pd

from app.models import User
from app.auth import get_password_hash

def test_upload_excel(client, db):
    # Create a dummy excel file in memory
    df = pd.DataFrame([
        {"Date": "2024-01-01", "Fleet": "1001", "Amount": 5000},
        {"Date": "2024-01-02", "Fleet": "1002", "Amount": 7500}
    ])
    
    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    excel_file.seek(0)
    
    # Create admin via DB
    admin = User(username="admin", hashed_password=get_password_hash("password"), role="admin")
    db.add(admin)
    db.commit()
    
    login_res = client.post("/auth/token", data={"username": "admin", "password": "password"})
    token = login_res.json()["access_token"]
    
    response = client.post(
        "/files/upload",
        files=[("files", ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))],
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert "processing complete" in response.json()["message"]

def test_upload_invalid_format(client, db):
    # Create admin via DB
    admin = User(username="admin2", hashed_password=get_password_hash("password"), role="admin")
    db.add(admin)
    db.commit()
    
    login_res = client.post("/auth/token", data={"username": "admin2", "password": "password"})
    token = login_res.json()["access_token"]
    
    response = client.post(
        "/files/upload",
        files=[("files", ("test.txt", io.BytesIO(b"not an excel"), "text/plain"))],
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "Import failed" in response.json()["detail"]
