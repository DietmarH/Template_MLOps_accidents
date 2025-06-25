import numpy as np
import bentoml
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio

# Secret key and algorithm for JWT authentication
JWT_SECRET_KEY = "your_jwt_secret_key_here"
JWT_ALGORITHM = "HS256"

# User credentials for authentication
USERS = {
    "user123": "password123",
    "user456": "password456"
}

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path == "/classify":
            token = request.headers.get("Authorization")
            if not token:
                return JSONResponse(status_code=401, content={"detail": "Missing authentication token"})

            try:
                token = token.split()[1]  # Remove 'Bearer ' prefix
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            except jwt.ExpiredSignatureError:
                return JSONResponse(status_code=401, content={"detail": "Token has expired"})
            except jwt.InvalidTokenError:
                return JSONResponse(status_code=401, content={"detail": "Invalid token"})

            request.state.user = payload.get("sub")

        response = await call_next(request)
        return response

# Pydantic model to validate input data
class InputModel(BaseModel):
    place: int
    catu: int
    sexe: int
    secu1: float
    year_acc: int
    victim_age: int
    catv: int
    obsm: int
    motor: int
    catr: int
    circ: int
    surf: int
    situ: int
    vma: int
    jour: int
    mois: int
    lum: int
    dep: int
    com: int
    agg_: int
    int: int
    atm: int
    col: int
    lat: float
    long: float
    hour: int
    nb_victim: int
    nb_vehicules: int

# Function to create a JWT token
def create_jwt_token(user_id: str):
    expiration = datetime.utcnow() + timedelta(hours=1)
    payload = {
        "sub": user_id,
        "exp": expiration
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

# Get the model from the Model Store  
accidents_rf_model = bentoml.sklearn.get("accidents_rf:latest")

@bentoml.service(
    name="rf_clf_service",
    resources={"cpu": "2"},
)
class AccidentClassificationService:
    
    def __init__(self):
        self.model = accidents_rf_model.load_model()
    
    @bentoml.api
    def login(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        username = credentials.get("username")
        password = credentials.get("password")

        if username in USERS and USERS[username] == password:
            token = create_jwt_token(username)
            return {"token": token}
        else:
            raise bentoml.exceptions.BadInput("Invalid credentials")

    @bentoml.api
    def classify(self, input_data: InputModel) -> Dict[str, Any]:
        # Convert the input data to a numpy array
        input_series = np.array([
            input_data.place, input_data.catu, input_data.sexe, input_data.secu1,
            input_data.year_acc, input_data.victim_age, input_data.catv, input_data.obsm,
            input_data.motor, input_data.catr, input_data.circ, input_data.surf,
            input_data.situ, input_data.vma, input_data.jour, input_data.mois,
            input_data.lum, input_data.dep, input_data.com, input_data.agg_,
            input_data.int, input_data.atm, input_data.col, input_data.lat,
            input_data.long, input_data.hour, input_data.nb_victim, input_data.nb_vehicules
        ])

        result = self.model.predict(input_series.reshape(1, -1))

        return {
            "prediction": result.tolist()
        }
