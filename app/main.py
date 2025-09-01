from fastapi import FastAPI
from app.database import engine, Base
from app.endpoints import organizations, users, auth, ice_rinks, measurements

# Zakomentowane, ponieważ baza jest zarządzana przez skrypt SQL
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Centralny System Zarządzania Energią dla Lodowisk",
    description="API do zarządzania danymi z lodowisk.",
    version="1.0.0 (dev)"
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(organizations.router, prefix="/api/organizations", tags=["Organizations"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(ice_rinks.router, prefix="/api/ice-rinks", tags=["Ice Rinks"])
app.include_router(measurements.router, prefix="/api/ice-rinks", tags=["Measurements"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Witaj w API Systemu Zarządzania Energią dla Lodowisk!"}
