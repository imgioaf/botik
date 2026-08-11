from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import secrets, os, requests
from database import engine, get_db, Base, SessionLocal
from models import User, Balance, Transaction, WithdrawReq
from security import validate_init_data, BOT_TOKEN

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Switzer Wallet API")
app.add_middleware(CORSMiddleware, allow_origins=["https://imgioaf.github.io"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class SendTx(BaseModel):
    coin: str
    to: str
    amount: float

def notify(uid, text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": uid, "text": text}, timeout=5)
    except Exception:
        pass

def ensure_user(db, tg_user):
    u = db.query(User).filter(User.id == tg_user["id"]).first()
    if not u:
        u = User(id=tg_user["id"], username=tg_user.get("username"),
                 first_name=tg_user.get("first_name", "User"),
                 address="0x" + secrets.token_hex(20))
        db.add(u)
        for c in ["USDT", "BTC", "ETH"]:
            db.add(Balance(user_id=u.id, coin=c, amount=100.0 if c == "USDT" else 0.01))
        db.commit()
        db.refresh(u)
    return u

@app.get("/api/wallet")
def get_wallet(user: dict = Depends(validate_init_data), db: Session = Depends(get_db)):
    u = ensure_user(db, user)
    balances = db.query(Balance).filter(Balance.user_id == u.id).all()
    txs = db.query(Transaction).filter(Transaction.user_id == u.id).order_by(Transaction.id.desc()).limit(20).all()
    prices = {"USDT": 1.0, "BTC": 65000.0, "ETH": 3500.0}
    total = sum(b.amount * prices.get(b.coin, 0) for b in balances)
    return {
        "total_usd": total,
        "address": u.address,
        "coins": [{"sym": b.coin, "amount": round(b.amount, 6)} for b in balances],
        "tx": [{"coin": t.coin, "amount": t.amount, "dir": t.direction} for t in txs],
    }

@app.post("/api/wallet/send")
def send_tx(p: SendTx, user: dict = Depends(validate_init_data), db: Session = Depends(get_db)):
    u = ensure_user(db, user)
    b = db.query(Balance).filter(Balance.user_id == u.id, Balance.coin == p.coin).first()
    if not b or b.amount < p.amount:
        raise HTTPException(400, "Not enough funds")
    b.amount -= p.amount
    db.add(Transaction(user_id=u.id, coin=p.coin, amount=p.amount, direction="out", to_addr=p.to))
    db.commit()
    notify(u.id, f"✅ Заявка на вывод создана\n{p.amount} {p.coin}\nАдрес: {p.to[:8]}…{p.to[-6:]}")
    return {"ok": True, "txid": secrets.token_hex(16)}

CG_IDS = "bitcoin,ethereum,tether,usd-coin,toncoin,solana,binancecoin,ripple,tron,litecoin,dogecoin,cardano,avalanche-2,polygon-ecosystem-token,polkadot,cosmos,pepe,notcoin"

@app.get("/api/prices")
def prices():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price",
            params={"ids": CG_IDS, "vs_currencies": "usd", "include_24hr_change": "true"}, timeout=10)
        return r.json()
    except Exception:
        return {}

# ===== БЛОК D: TON-депозиты и заявки на вывод =====
TON_DEPOSIT = os.getenv("TON_DEPOSIT_ADDRESS", "")

@app.get("/api/deposit")
def deposit_info(user: dict = Depends(validate_init_data)):
    return {"ton_address": TON_DEPOSIT, "code": str(user["id"])}

@app.post("/api/withdraw")
def withdraw_req(p: SendTx, user: dict = Depends(validate_init_data), db: Session = Depends(get_db)):
    u = ensure_user(db, user)
    b = db.query(Balance).filter(Balance.user_id == u.id, Balance.coin == p.coin).first()
    if not b or b.amount < p.amount:
        raise HTTPException(400, "Not enough funds")
    b.amount -= p.amount
    db.add(WithdrawReq(user_id=u.id, coin=p.coin, amount=p.amount, to_addr=p.to, status="pending"))
    db.add(Transaction(user_id=u.id, coin=p.coin, amount=p.amount, direction="out", to_addr=p.to))
    db.commit()
    notify(u.id, f"📨 Заявка на вывод {p.amount} {p.coin} создана. Ожидает модерации.")
    return {"ok": True, "status": "pending"}

@app.get("/api/admin/pending")
def admin_pending(admin: str = Header(alias="X-Admin-Token")):
    if admin != os.getenv("ADMIN_TOKEN", ""):
        raise HTTPException(403, "Forbidden")
    db = SessionLocal()
    rows = db.query(WithdrawReq).filter(WithdrawReq.status == "pending").all()
    db.close()
    return [{"id": r.id, "user": r.user_id, "coin": r.coin, "amount": r.amount, "to": r.to_addr} for r in rows]

@app.post("/api/admin/approve/{rid}")
def admin_approve(rid: int, admin: str = Header(alias="X-Admin-Token")):
    if admin != os.getenv("ADMIN_TOKEN", ""):
        raise HTTPException(403, "Forbidden")
    db = SessionLocal()
    r = db.query(WithdrawReq).filter(WithdrawReq.id == rid).first()
    if r:
        r.status = "approved"
        db.commit()
        notify(r.user_id, f"✅ Вывод {r.amount} {r.coin} одобрен и выполнен!")
    db.close()
    return {"ok": True}
