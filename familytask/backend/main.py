import hashlib  # Importe les primitives de dérivation de clé.
import hmac  # Compare les empreintes sans fuite temporelle exploitable.
import os  # Importe le module permettant de lire les variables d'environnement.
import secrets  # Génère les sels et jetons imprévisibles.
import threading
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request, Response  # Importe les outils HTTP de FastAPI.
from fastapi.middleware.cors import CORSMiddleware  # Importe le middleware qui autorise les requêtes du front-end.
from pydantic import BaseModel
from sqlalchemy import inspect, text
from sqlmodel import Field, Session, SQLModel, create_engine, select  # Importe les outils SQLModel nécessaires au modèle et à la base.

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///familytask.db")  # Récupère l'adresse de la base ou utilise SQLite localement.
APP_ENV = os.getenv("APP_ENV", "development").lower()  # Distingue le développement de la production.
SESSION_COOKIE = "familytask_session"  # Nom du cookie de session inaccessible au JavaScript.
AUTH_RATE_LIMIT = 5  # Nombre maximal d'échecs d'authentification dans la fenêtre définie.
AUTH_RATE_WINDOW = 15 * 60  # Durée de la fenêtre de limitation, en secondes.
auth_attempts: defaultdict[str, deque[float]] = defaultdict(deque)
auth_attempts_lock = threading.Lock()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}  # Configure SQLite pour accepter les accès de FastAPI.
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)  # Crée le moteur de connexion à la base de données.


class Task(SQLModel, table=True):  # Déclare le modèle SQLModel représentant une tâche.
    id: int | None = Field(default=None, primary_key=True)  # Définit l'identifiant entier généré automatiquement et clé primaire.
    owner_id: int | None = Field(default=None, foreign_key="member.id", index=True)
    member_id: int | None = Field(default=None, foreign_key="member.id", index=True)
    family_code: str | None = Field(default=None, index=True)
    title: str  # Définit le texte de la tâche.
    done: bool = False  # Définit l'état de la tâche, faux par défaut.


class Member(SQLModel, table=True):  # Déclare le modèle SQLModel représentant un membre de la famille.
    id: int | None = Field(default=None, primary_key=True)  # Définit l'identifiant entier généré automatiquement et clé primaire.
    email: str = Field(unique=True, index=True)  # Définit l'adresse email unique et indexée du membre.
    name: str  # Définit le nom du membre.
    lien: str  # Définit le lien familial du membre.
    is_admin: bool = False  # Définit le statut administrateur, faux par défaut.
    family_code: str = Field(index=True)  # Définit le code de famille indexé.
    password_hash: str  # Stocke une empreinte PBKDF2 salée du mot de passe.
    token: str | None = None  # Stocke le jeton de session actif, s'il existe.


class AuthRequest(BaseModel):
    email: str
    password: str
    name: str | None = None
    family: str | None = None
    lien: str | None = None


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
    return f"pbkdf2_sha256$600000${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def hash_token(token: str) -> str:
    # Une empreinte SHA-256 suffit pour un token déjà généré par secrets.token_urlsafe.
    return "sha256$" + hashlib.sha256(token.encode("utf-8")).hexdigest()


def set_session_cookie(response: Response, token: str) -> None:
    # Le cookie HttpOnly empêche le JavaScript du navigateur de lire le token.
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=APP_ENV == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )


def rate_limit_key(request: Request, email: str) -> tuple[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}", f"email:{email}"


def reject_if_rate_limited(request: Request, email: str) -> tuple[str, str]:
    # Limite à la fois une adresse IP et une adresse email pour freiner le brute force.
    keys = rate_limit_key(request, email)
    now = time.monotonic()
    with auth_attempts_lock:
        for key in keys:
            attempts = auth_attempts[key]
            while attempts and now - attempts[0] >= AUTH_RATE_WINDOW:
                attempts.popleft()
            if len(attempts) >= AUTH_RATE_LIMIT:
                raise HTTPException(status_code=429, detail="Trop de tentatives, réessayez plus tard")
    return keys


def record_failed_auth(keys: tuple[str, str]) -> None:
    now = time.monotonic()
    with auth_attempts_lock:
        for key in keys:
            auth_attempts[key].append(now)


def clear_auth_attempts(keys: tuple[str, str]) -> None:
    with auth_attempts_lock:
        for key in keys:
            auth_attempts.pop(key, None)


def public_member(member: Member) -> dict[str, object]:
    return {
        "id": member.id,
        "email": member.email,
        "name": member.name,
        "lien": member.lien,
        "is_admin": member.is_admin,
        "family_code": member.family_code,
    }


def get_session():
    with Session(engine) as session:
        yield session


def current_member(
    authorization: Optional[str] = Header(None),
    session_cookie: Optional[str] = Cookie(None, alias=SESSION_COOKIE),
    session: Session = Depends(get_session),
) -> Member:
    scheme, _, token = (authorization or "").partition(" ")
    token = token if scheme.lower() == "bearer" else session_cookie
    member = None
    if token:
        member = session.exec(select(Member).where(Member.token == hash_token(token))).first()
    if member is None:
        raise HTTPException(status_code=401, detail="Authentification requise")
    return member


app = FastAPI(title="FamilyTask")  # Crée l'application FastAPI.
allowed_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]
if APP_ENV == "production" and "*" in allowed_origins:
    raise RuntimeError("CORS_ORIGINS doit expliciter les origines en production")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.on_event("startup")  # Demande l'exécution de la fonction lors du démarrage de l'application.
def create_tables():  # Déclare la fonction qui crée les tables manquantes.
    SQLModel.metadata.create_all(engine)  # Crée la table Task dans la base de données.
    with Session(engine) as session:
        # Hache une seule fois les tokens éventuels issus d'une version précédente.
        for member in session.exec(select(Member)).all():
            if member.token and not member.token.startswith("sha256$"):
                member.token = hash_token(member.token)
                session.add(member)
        session.commit()
        task_columns = {column["name"] for column in inspect(engine).get_columns("task")}
        if "owner_id" not in task_columns:
            session.exec(text("ALTER TABLE task ADD COLUMN owner_id INTEGER"))
            session.commit()
        session.exec(text("CREATE INDEX IF NOT EXISTS ix_task_owner_id ON task (owner_id)"))
        if "member_id" not in task_columns:
            session.exec(text("ALTER TABLE task ADD COLUMN member_id INTEGER"))
            session.commit()
        if "family_code" not in task_columns:
            session.exec(text("ALTER TABLE task ADD COLUMN family_code VARCHAR"))
            session.commit()
        session.exec(text("UPDATE task SET member_id = owner_id WHERE member_id IS NULL"))
        session.exec(text(
            "UPDATE task SET family_code = "
            "(SELECT family_code FROM member WHERE member.id = task.member_id) "
            "WHERE family_code IS NULL"
        ))
        session.exec(text("CREATE INDEX IF NOT EXISTS ix_task_member_id ON task (member_id)"))
        session.exec(text("CREATE INDEX IF NOT EXISTS ix_task_family_code ON task (family_code)"))
        session.commit()


@app.get("/api/health")  # Enregistre la route de contrôle de santé de l'API.
def health():  # Déclare la route de vérification de l'état de l'API.
    return {"status": "ok"}  # Retourne un état positif pour confirmer que l'API fonctionne.

@app.post("/api/signup")
def signup(credentials: AuthRequest, response: Response) -> dict[str, object]:
    # Le premier compte créé constitue la famille et en devient l'administrateur.
    email = credentials.email.strip().lower()
    if (
        not email
        or len(credentials.password) < 8
        or not credentials.name
        or not credentials.name.strip()
        or not credentials.family
        or not credentials.family.strip()
        or not credentials.lien
        or not credentials.lien.strip()
    ):
        raise HTTPException(status_code=422, detail="Email, mot de passe, nom, famille et lien requis")
    with Session(engine) as session:
        if session.exec(select(Member).where(Member.email == email)).first():
            raise HTTPException(status_code=409, detail="Cet email est déjà utilisé")
        member = Member(
            email=email,
            name=credentials.name.strip(),
            lien=credentials.lien.strip(),
            is_admin=True,
            family_code="fam-" + secrets.token_hex(8),
            password_hash=hash_password(credentials.password),
        )
        raw_token = secrets.token_urlsafe(32)
        member.token = hash_token(raw_token)
        session.add(member)
        session.commit()
        session.refresh(member)
        set_session_cookie(response, raw_token)
        return {"token": raw_token, "member": public_member(member)}


@app.post("/api/login")
def login(credentials: AuthRequest, request: Request, response: Response) -> dict[str, object]:
    email = credentials.email.strip().lower()
    attempt_keys = reject_if_rate_limited(request, email)
    with Session(engine) as session:
        member = session.exec(select(Member).where(Member.email == email)).first()
        if member is None or not verify_password(credentials.password, member.password_hash):
            record_failed_auth(attempt_keys)
            raise HTTPException(status_code=401, detail="Identifiants invalides")
        raw_token = secrets.token_urlsafe(32)
        member.token = hash_token(raw_token)
        session.add(member)
        session.commit()
        clear_auth_attempts(attempt_keys)
        set_session_cookie(response, raw_token)
        return {"token": raw_token, "member": public_member(member)}


@app.get("/api/me")
def me(member: Member = Depends(current_member)):
    # Retourne uniquement les informations publiques du membre connecté.
    return public_member(member)


@app.get("/api/members")
def list_members(member: Member = Depends(current_member), session: Session = Depends(get_session)):
    return [
        public_member(family_member)
        for family_member in session.exec(
            select(Member).where(Member.family_code == member.family_code)
        ).all()
    ]


@app.post("/api/logout")
def logout(response: Response, member: Member = Depends(current_member), session: Session = Depends(get_session)):
    # Invalide le jeton en le supprimant de la base de données.
    member.token = None
    session.add(member)
    session.commit()
    if response:
        response.delete_cookie(SESSION_COOKIE)
    return {"message": "Déconnexion réussie"}


@app.get("/api/tasks", response_model=list[Task])  # Enregistre la route qui retourne toutes les tâches.
def get_tasks(member: Member = Depends(current_member)):  # Déclare la route de récupération des tâches.
    with Session(engine) as session:  # Ouvre une session SQLModel pour interroger la base de données.
        tasks = session.exec(select(Task).where(
            Task.family_code == member.family_code,
            Task.member_id == member.id,
        )).all()  # Récupère uniquement les tâches assignées au membre connecté.
    return tasks  # Retourne les tâches sous forme de liste.


@app.get("/api/tasks/famille", response_model=list[Task])
def get_family_tasks(member: Member = Depends(current_member)):
    if not member.is_admin:
        raise HTTPException(status_code=403, detail="Seul l'admin peut voir les tâches de la famille")
    with Session(engine) as session:
        return session.exec(select(Task).where(Task.family_code == member.family_code)).all()


@app.post("/api/tasks", response_model=Task)  # Enregistre la route de création d'une tâche.
def create_task(title: str, member_id: int | None = None,
                member: Member = Depends(current_member)):  # Reçoit le titre et l'éventuel membre assigné.
    if not title.strip():  # Refuse les titres vides ou composés uniquement d'espaces.
        raise HTTPException(status_code=422, detail="Le titre de la tâche ne peut pas être vide")  # Signale un titre invalide.
    assignee_id = member.id
    if member.is_admin and member_id is not None:
        with Session(engine) as session:
            assignee = session.get(Member, member_id)
            if assignee is None or assignee.family_code != member.family_code:
                raise HTTPException(status_code=404, detail="Membre de la famille introuvable")
        assignee_id = member_id
    task = Task(
        owner_id=member.id,
        member_id=assignee_id,
        family_code=member.family_code,
        title=title,
        done=False,
    )  # Crée une tâche pour le membre connecté ou l'assigné choisi par un admin.
    with Session(engine) as session:  # Ouvre une session pour enregistrer la tâche.
        session.add(task)  # Ajoute la tâche à la session.
        session.commit()  # Enregistre la tâche dans la base de données.
        session.refresh(task)  # Récupère l'identifiant généré par la base.
    return task  # Retourne la tâche créée avec son identifiant.


@app.patch("/api/tasks/{task_id}", response_model=Task)  # Enregistre la route qui inverse l'état d'une tâche.
def toggle_task(task_id: int, member: Member = Depends(current_member)):  # Reçoit l'identifiant de la tâche à modifier.
    with Session(engine) as session:  # Ouvre une session pour rechercher et modifier la tâche.
        task = session.get(Task, task_id)  # Recherche la tâche à partir de son identifiant.
        if task is None or task.family_code != member.family_code or task.member_id != member.id:  # Empêche l'accès aux tâches d'un autre membre.
            raise HTTPException(status_code=404, detail="Tâche introuvable")  # Signale que l'identifiant est inconnu.
        task.done = not task.done  # Bascule l'état terminé de la tâche.
        session.add(task)  # Prépare la tâche modifiée pour l'enregistrement.
        session.commit()  # Enregistre le nouvel état dans la base de données.
        session.refresh(task)  # Recharge la tâche modifiée avant de la retourner.
    return task  # Retourne la tâche dont l'état a été basculé.


@app.delete("/api/tasks/{task_id}")  # Enregistre la route de suppression d'une tâche.
def delete_task(task_id: int, member: Member = Depends(current_member)):  # Reçoit l'identifiant de la tâche à supprimer.
    with Session(engine) as session:  # Ouvre une session pour rechercher et supprimer la tâche.
        task = session.get(Task, task_id)  # Recherche la tâche à partir de son identifiant.
        if task is None or task.family_code != member.family_code or task.member_id != member.id:  # Empêche la suppression d'une tâche d'un autre membre.
            raise HTTPException(status_code=404, detail="Tâche introuvable")  # Signale que l'identifiant est inconnu.
        session.delete(task)  # Supprime la tâche de la session et de la base de données.
        session.commit()  # Enregistre définitivement la suppression.
    return {"message": "Tâche supprimée avec succès"}  # Confirme la suppression de la tâche.
