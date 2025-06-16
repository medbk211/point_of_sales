import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app  
from app.core.database import get_db
from app.models import Base
from app.schemas.employee import EmployeeCreate
from app.crud.employee import add_employee


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# ✅ Test 1: قراءة الموظفين لما تكون القائمة فارغة
def test_read_employees_empty():
    response = client.get("/employees")
    assert response.status_code == 200
    assert response.json() == []

# ✅ Test 2: نضيف موظف ونشوف إذا موجود
def test_create_and_read_employee():
    # نجهز بيانات الموظف
    new_employee = {
        "first_name": "Mohamed",
        "last_name": "Briki",
        "email": "mohamed@example.com",
        "password": "123456",
        "confirm_password": "123456"
    }

    # نعمل POST للموظف
    res = client.post("/employees", json=new_employee)
    assert res.status_code == 201
    employee_id = res.json()["id"]

    # نعمل GET ونشوف إذا الموظف موجود
    res_get = client.get("/employees")
    assert res_get.status_code == 200
    employees = res_get.json()
    assert len(employees) == 1
    assert employees[0]["id"] == employee_id
    assert employees[0]["email"] == "mohamed@example.com"
