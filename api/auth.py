import os
import sqlite3
import secrets
import hashlib
import hmac
from pathlib import Path
from datetime import datetime, timezone, timedelta


AUTH_DB = Path(
    os.environ.get(
        "KULZZY_AUTH_DB",
        "/kulzzy/auth/kulzzy_auth.db"
    )
).resolve()


SESSION_HOURS = 12


def ensure_database():

    AUTH_DB.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with sqlite3.connect(AUTH_DB) as db:

        db.execute("""
            CREATE TABLE IF NOT EXISTS administrators (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                username TEXT UNIQUE NOT NULL,

                password_hash TEXT NOT NULL,

                role TEXT NOT NULL DEFAULT 'owner',

                active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT NOT NULL

            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (

                token_hash TEXT PRIMARY KEY,

                admin_id INTEGER NOT NULL,

                expires_at TEXT NOT NULL,

                created_at TEXT NOT NULL,

                FOREIGN KEY(admin_id)
                    REFERENCES administrators(id)

            )
        """)

        db.commit()


def hash_password(password):

    salt = secrets.token_bytes(32)

    password_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1
    )

    return (
        salt.hex() +
        ":" +
        password_hash.hex()
    )


def verify_password(
    password,
    stored_hash
):

    try:

        salt_hex, hash_hex = (
            stored_hash.split(":")
        )

        salt = bytes.fromhex(
            salt_hex
        )

        expected = bytes.fromhex(
            hash_hex
        )

        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=16384,
            r=8,
            p=1
        )

        return hmac.compare_digest(
            actual,
            expected
        )

    except Exception:

        return False


def create_admin(
    username,
    password,
    role="owner"
):

    ensure_database()

    password_hash = hash_password(
        password
    )

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    with sqlite3.connect(AUTH_DB) as db:

        db.execute(
            """
            INSERT INTO administrators
            (
                username,
                password_hash,
                role,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                username,
                password_hash,
                role,
                created_at
            )
        )

        db.commit()


def authenticate(
    username,
    password
):

    ensure_database()

    with sqlite3.connect(AUTH_DB) as db:

        row = db.execute(
            """
            SELECT
                id,
                username,
                password_hash,
                role
            FROM administrators
            WHERE username = ?
            AND active = 1
            """,
            (username,)
        ).fetchone()

    if not row:

        return None

    admin_id = row[0]

    stored_hash = row[2]

    if not verify_password(
        password,
        stored_hash
    ):

        return None

    token = secrets.token_urlsafe(
        48
    )

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    expires = (
        datetime.now(timezone.utc)
        +
        timedelta(
            hours=SESSION_HOURS
        )
    ).isoformat()

    created = datetime.now(
        timezone.utc
    ).isoformat()

    with sqlite3.connect(AUTH_DB) as db:

        db.execute(
            """
            INSERT INTO sessions
            (
                token_hash,
                admin_id,
                expires_at,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                token_hash,
                admin_id,
                expires,
                created
            )
        )

        db.commit()

    return {

        "token":
            token,

        "admin_id":
            admin_id,

        "username":
            row[1],

        "role":
            row[3],

        "expires_at":
            expires

    }


def get_session(token):

    if not token:

        return None

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    now = datetime.now(
        timezone.utc
    )

    with sqlite3.connect(AUTH_DB) as db:

        row = db.execute(
            """
            SELECT
                administrators.id,
                administrators.username,
                administrators.role,
                sessions.expires_at
            FROM sessions
            JOIN administrators
                ON administrators.id =
                   sessions.admin_id
            WHERE sessions.token_hash = ?
            AND administrators.active = 1
            """,
            (token_hash,)
        ).fetchone()

    if not row:

        return None

    try:

        expires = datetime.fromisoformat(
            row[3]
        )

    except Exception:

        return None

    if expires <= now:

        revoke_session(token)

        return None

    return {

        "admin_id":
            row[0],

        "username":
            row[1],

        "role":
            row[2],

        "expires_at":
            row[3]

    }


def revoke_session(token):

    if not token:

        return

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    with sqlite3.connect(AUTH_DB) as db:

        db.execute(
            """
            DELETE FROM sessions
            WHERE token_hash = ?
            """,
            (token_hash,)
        )

        db.commit()


def cleanup_sessions():

    ensure_database()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    with sqlite3.connect(AUTH_DB) as db:

        db.execute(
            """
            DELETE FROM sessions
            WHERE expires_at <= ?
            """,
            (now,)
        )

        db.commit()


if __name__ == "__main__":

    ensure_database()

    print(
        "Kulzzy authentication database ready."
  )
