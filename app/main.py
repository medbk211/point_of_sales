from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.routes import employee
from app.routes import auth



app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employee.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

