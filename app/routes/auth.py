from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import uuid

from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated


from app.repositories.employee import get_employee_email,confirmation_change_password,get_confirmation_code_change_password,get_confirmation_code
from app.core.database import get_db
from app.core.config import settings

from app.models import Employee, ChangePasword,Acount_Activation



from app.schemas.employee import  ConfirmResetPasswordRequest, ConfirmResetPasswordResponse, ResetPasswordRequest, ResetPasswordResponse, SetPasswordInput, ConfirmationResponse,PasswordChangeRequest
from app.enums import TokenStatusEnum, StatusAccountEnum, RoleEnum

router = APIRouter()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

def generate_token():
    token = str(uuid.uuid4())
    return  token

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, username: str, password: str):
    user = get_employee_email(db, email=username)
    if not user or not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = get_employee_email(db, email=username)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception


async def get_current_active_user(
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user




    
@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(current_user: Annotated[Employee, Depends(get_current_active_user)]):
    return current_user


# Employee changes password (authenticated)
@router.put("/employees/change-password")
def password_change(data_entry: PasswordChangeRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    employee = get_current_user(token, db)
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    employee_in_db = db.query(Employee).filter(Employee.id == employee.id).first()
    if not employee_in_db:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not verify_password(data_entry.current_password, employee_in_db.password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    if data_entry.new_password != data_entry.confirm_new_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")

    hashed_password = pwd_context.hash(data_entry.new_password)
    employee_in_db.password = hashed_password
    db.commit()
    return {"message": "Password updated successfully."}
    
# Request to reset password (send email)
@router.post("/employees/reset_password", response_model=ConfirmResetPasswordResponse, status_code=201)
def reset_password(confirmation_data: ConfirmResetPasswordRequest, db: Session = Depends(get_db)):
    employee_data = get_employee_email(db, email=confirmation_data.email)
    if not employee_data:
        raise HTTPException(status_code=404, detail="Employee not found")
    confirmation_change_password(db, employee_data)
    return ConfirmResetPasswordResponse(status_code=200, detail="Reset password email sent")    

# Confirm reset password (with token and new password)
@router.patch("/employees/confirm_reset_password", response_model=ResetPasswordResponse, status_code=200)
def confirmation_reset_password(confirmation_input: ResetPasswordRequest, db: Session = Depends(get_db)):
    confirmation_code = get_confirmation_code_change_password(db, confirmation_input.token)
    if not confirmation_code:
        raise HTTPException(status_code=404, detail="Confirmation code not found")
    if confirmation_code.token_status_id == TokenStatusEnum.Expired:
        raise HTTPException(status_code=400, detail="Confirmation code expired")
    if confirmation_input.password != confirmation_input.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    hashed_password = pwd_context.hash(confirmation_input.password)
    db.query(ChangePasword).filter(ChangePasword.id == confirmation_code.id).update({"token_status_id": TokenStatusEnum.Expired})
    db.query(Employee).filter(Employee.id == confirmation_code.Employee_id).update({"password": hashed_password})
    db.commit()
    return ResetPasswordResponse(status_code=200, detail="Password changed successfully")


# Set initial password and activate account
@router.post("/employees/set_password", response_model=ConfirmationResponse, status_code=200)
def set_password(input: SetPasswordInput, db: Session = Depends(get_db)):
    confirmation_code = get_confirmation_code(db, input.token)
    if not confirmation_code:
        raise HTTPException(status_code=404, detail="Confirmation code not found")
    if confirmation_code.token_status_id == TokenStatusEnum.Expired:
        raise HTTPException(status_code=400, detail="Confirmation code expired")
    if input.password != input.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    hashed_pw = pwd_context.hash(input.password)
    db.query(Employee).filter(Employee.id == confirmation_code.Employee_id).update({
        "password": hashed_pw,
        "status_account": StatusAccountEnum.Active
    })
    db.query(Acount_Activation).filter(Acount_Activation.id == confirmation_code.id).update({
        "token_status_id": TokenStatusEnum.Expired
    })
    db.commit()
    return ConfirmationResponse(status_code=200, detail="Password set, account activated.")

