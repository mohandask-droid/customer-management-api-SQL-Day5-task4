import hashlib
import hmac
from typing import Optional

from fastapi import (BackgroundTasks, Depends, FastAPI, Header,
                     HTTPException, Request)
from sqlalchemy.orm import Session

from src import config, database
from src.database import Base, engine, get_db
from src.models import Customer, Event
from src.schemas import CustomerCreate, CustomerOut

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Customer Management API")


def verify_api_key(x_api_key: Optional[str] = Header(default=None)):
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.post("/customers", response_model=CustomerOut, status_code=201,
          dependencies=[Depends(verify_api_key)])
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    if db.query(Customer).filter_by(email=data.email).first():
        raise HTTPException(status_code=409, detail="Email already exists")
    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@app.get("/customers", response_model=list[CustomerOut],
         dependencies=[Depends(verify_api_key)])
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).all()


@app.get("/customers/{customer_id}", response_model=CustomerOut,
         dependencies=[Depends(verify_api_key)])
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.put("/customers/{customer_id}", response_model=CustomerOut,
         dependencies=[Depends(verify_api_key)])
def update_customer(customer_id: int, data: CustomerCreate,
                    db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    clash = db.query(Customer).filter(Customer.email == data.email,
                                      Customer.id != customer_id).first()
    if clash:
        raise HTTPException(status_code=409, detail="Email already exists")
    for key, value in data.model_dump().items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return customer


@app.delete("/customers/{customer_id}", status_code=204,
            dependencies=[Depends(verify_api_key)])
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(customer)
    db.commit()


def save_event(raw_body: bytes):
    db = database.SessionLocal()
    try:
        db.add(Event(payload=raw_body.decode("utf-8", errors="replace")))
        db.commit()
    finally:
        db.close()


@app.post("/webhooks/customer-events")
async def customer_events(request: Request, background_tasks: BackgroundTasks,
                          x_signature: Optional[str] = Header(default=None)):
    raw_body = await request.body()          # raw bytes, not parsed JSON
    if not x_signature:
        raise HTTPException(status_code=401, detail="Invalid signature")
    expected = hmac.new(config.WEBHOOK_SECRET.encode(), raw_body,
                        hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    background_tasks.add_task(save_event, raw_body)   # runs after response
    return {"status": "accepted"}