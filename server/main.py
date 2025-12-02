from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from datetime import datetime, timedelta, UTC
import jwt
from jwt.exceptions import InvalidTokenError
from collections import defaultdict
from dotenv import load_dotenv
import os
import psycopg

load_dotenv() 

# ask adib for .env file 
# put .env file in /server directory
JWT_KEY = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", "1"))
DATABASE_URL = os.getenv("DATABASE_URL")

password_hasher = PasswordHasher()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# conn = psycopg.connect(DATABASE_URL)
conn = psycopg.connect(DATABASE_URL, autocommit=True)
def get_user_from_db(username: str):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT u.id, u.username, c.password_hash
            FROM users u
            JOIN auth_local_credentials c ON c.user_id = u.id
            WHERE u.username = %s
        """, (username,))
        
        row = cur.fetchone()
        if row is None:
            return None
        
        user_id, username, password_hash = row
        return {
            "id": user_id,
            "username": username,
            "password_hash": password_hash
        }


async def get_current_user(token: str):
    try:
        claims = jwt.decode(token, JWT_KEY, algorithms=[JWT_ALGORITHM])
        username = claims.get("sub")
        user = get_user_from_db(username)
        if user is None:
            raise InvalidTokenError
        return user
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user_dep(
    token: Annotated[str, Depends(oauth2_scheme)]
):
    return await get_current_user(token)

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    bad_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Bad credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    user = get_user_from_db(form_data.username)
    if user is None:
        raise bad_credentials
    try:
        password_hasher.verify(user["password_hash"], form_data.password)
    except Exception:
        raise bad_credentials
    return {
        "access_token": jwt.encode({
            "sub": form_data.username, "exp": datetime.now(UTC) + timedelta(hours=1)
        }, JWT_KEY, JWT_ALGORITHM),
        "token_type": "bearer"
    }


active_connections = defaultdict(set)

@app.websocket("/chat/{chat_id}")
async def chat(websocket: WebSocket, chat_id: str):
    chat_id = int(chat_id)
    user = await get_current_user(websocket.query_params.get("token"))
    await websocket.accept()
    active_connections[chat_id].add(websocket)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT m.content, u.username, m.created_at, m.msg_type
            FROM messages m
            JOIN users u ON u.id = m.user_id
            WHERE m.session_id = %s
            ORDER BY m.created_at ASC
            LIMIT 50
        """, (chat_id,))
        history = cur.fetchall()

    for content, username, created_at, msg_type in history:
        await websocket.send_json({
            "history": True, 
            "message": content,
            "username": username,
            "tag": msg_type,
            "ts": created_at.isoformat()
        })

    try:
        while True:
            data = await websocket.receive_json()
            text = (data.get("message") or "").strip()
            msg_type = data.get("tag") or "chat"

            # Store message
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO messages (session_id, user_id, content, msg_type)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, created_at
                """, (chat_id, user["id"], text, msg_type))
                msg_id, created_at = cur.fetchone()
            conn.commit()
            
            for connection in active_connections[chat_id]:
                await connection.send_json({
                    "message": text,
                    "username": user["username"],
                    "tag": msg_type,
                    "ts": created_at.isoformat()
                })
    except WebSocketDisconnect:
        active_connections[chat_id].remove(websocket)

@app.get("/campaign/{campaign_id}/members")
async def list_campaign_members(campaign_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COALESCE(u.display_name, u.username) AS name
            FROM campaign_memberships cm
            JOIN users u
              ON u.id = cm.user_id
            WHERE cm.campaign_id = %s
              AND cm.role = 'PLAYER'
            ORDER BY name ASC;
            """,
            (campaign_id,)
        )

        rows = cur.fetchall()

    names = [r[0] for r in rows]
    return {"members": names}

@app.get("/campaigns/owned")
async def get_owned_campaigns(
    current_user: Annotated[dict, Depends(get_current_user_dep)]
):
    """
    Return all campaigns where owner_user_id = current_user['id'].
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, name, description
            FROM campaigns
            WHERE owner_user_id = %s
            ORDER BY id ASC
            """,
            (current_user["id"],),
        )
        rows = cur.fetchall()

    # Shape results as an array of objects
    campaigns = [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
        }
        for row in rows
    ]

    # Your frontend handles both plain array and { campaigns: [...] }.
    # Let's just return the plain array for simplicity.
    return campaigns

@app.get("/sessions")
async def get_user_sessions(
    current_user: Annotated[dict, Depends(get_current_user_dep)]
):
    """
    Return all sessions for campaigns the current user is part of
    (either campaign owner or in campaign_memberships).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT
                s.id,
                s.campaign_id,
                s.name,
                s.scheduled_at,
                s.started_at,
                s.ended_at,
                s.created_at,
                s.description
            FROM sessions s
            JOIN campaigns c
            ON c.id = s.campaign_id
            LEFT JOIN campaign_memberships cm
            ON cm.campaign_id = c.id
            WHERE cm.user_id = %s
            OR c.owner_user_id = %s
            ORDER BY
                s.scheduled_at NULLS LAST,
                s.created_at ASC
            """,
            (current_user["id"], current_user["id"]),
        )
        rows = cur.fetchall()

    sessions = [
        {
            "id": row[0],
            "campaign_id": row[1],
            "name": row[2],
            "scheduled_at": row[3].isoformat() if row[3] else None,
            "started_at":   row[4].isoformat() if row[4] else None,
            "ended_at":     row[5].isoformat() if row[5] else None,
            "created_at":   row[6].isoformat() if row[6] else None,
            "description":  row[7],
        }
        for row in rows
    ]

    return sessions

@app.post("/campaigns/{campaign_id}/invite/{username}")
async def invite_to_campaign(campaign_id: int, username: str):
    with conn.cursor() as cur:
        # 1. Look up user by username
        cur.execute(
            "SELECT id FROM users WHERE username = %s",
            (username,),
        )
        user_row = cur.fetchone()

        if user_row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_id = user_row[0]

        # 2. Insert membership (avoid duplicates with ON CONFLICT)
        cur.execute(
            """
            INSERT INTO campaign_memberships (campaign_id, user_id, role)
            VALUES (%s, %s, 'PLAYER')
            ON CONFLICT (campaign_id, user_id) DO NOTHING
            """,
            (campaign_id, user_id),
        )

    conn.commit()
    return {"status": "ok"}

@app.post("/sessions")
async def create_session(payload: dict):
    try:
        campaign_id = payload["campaign_id"]
        name = payload["name"]
        scheduled_at = payload.get("scheduled_at", None)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions (campaign_id, name, scheduled_at)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (campaign_id, name, scheduled_at),
            )
            session_id = cur.fetchone()[0]

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("create_session error:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="internal_error",
        )

    return {"status": "success", "session_id": session_id}

@app.post("/signup")
async def signup(payload):
    password_hash = password_hasher.hash(payload.password)

    try:
        with conn.cursor() as cur:
            # Insert into users first
            cur.execute(
                """
                INSERT INTO users (email, username, display_name)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (
                    payload.email,
                    payload.username,
                    payload.display_name or payload.username,
                ),
            )
            user_id = cur.fetchone()[0]

            # Insert into auth table
            cur.execute(
                """
                INSERT INTO auth_local_credentials (user_id, password_hash)
                VALUES (%s, %s);
                """,
                (user_id, password_hash),
            )

        conn.commit()

    except errors.UniqueViolation:
        conn.rollback()
        return {"status": "user_taken"}

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="internal_error"
        )

    return {"status": "success"}
