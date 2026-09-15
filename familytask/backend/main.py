import os  # Importe le module permettant de lire les variables d'environnement.

from fastapi import FastAPI, HTTPException  # Importe FastAPI et l'exception utilisée pour signaler une tâche introuvable.
from fastapi.middleware.cors import CORSMiddleware  # Importe le middleware qui autorise les requêtes du front-end.
from sqlmodel import Field, Session, SQLModel, create_engine, select  # Importe les outils SQLModel nécessaires au modèle et à la base.

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///familytask.db")  # Récupère l'adresse de la base ou utilise SQLite localement.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}  # Configure SQLite pour accepter les accès de FastAPI.
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)  # Crée le moteur de connexion à la base de données.


class Task(SQLModel, table=True):  # Déclare le modèle SQLModel représentant une tâche.
    id: int | None = Field(default=None, primary_key=True)  # Définit l'identifiant entier généré automatiquement et clé primaire.
    title: str  # Définit le texte de la tâche.
    done: bool = False  # Définit l'état de la tâche, faux par défaut.

app = FastAPI(title="FamilyTask")  # Crée l'application FastAPI.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])  # Autorise les appels du front-end.


@app.on_event("startup")  # Demande l'exécution de la fonction lors du démarrage de l'application.
def create_tables():  # Déclare la fonction qui crée les tables manquantes.
    SQLModel.metadata.create_all(engine)  # Crée la table Task dans la base de données.


@app.get("/api/health")  # Enregistre la route de contrôle de santé de l'API.
def health():  # Déclare la route de vérification de l'état de l'API.
    return {"status": "ok"}  # Retourne un état positif pour confirmer que l'API fonctionne.


@app.get("/api/tasks", response_model=list[Task])  # Enregistre la route qui retourne toutes les tâches.
def get_tasks():  # Déclare la route de récupération des tâches.
    with Session(engine) as session:  # Ouvre une session SQLModel pour interroger la base de données.
        tasks = session.exec(select(Task)).all()  # Récupère toutes les lignes de la table Task.
    return tasks  # Retourne les tâches sous forme de liste.


@app.post("/api/tasks", response_model=Task)  # Enregistre la route de création d'une tâche.
def create_task(title: str):  # Reçoit le titre transmis en paramètre de requête.
    if not title.strip():  # Refuse les titres vides ou composés uniquement d'espaces.
        raise HTTPException(status_code=422, detail="Le titre de la tâche ne peut pas être vide")  # Signale un titre invalide.
    task = Task(title=title, done=False)  # Crée une nouvelle tâche non terminée.
    with Session(engine) as session:  # Ouvre une session pour enregistrer la tâche.
        session.add(task)  # Ajoute la tâche à la session.
        session.commit()  # Enregistre la tâche dans la base de données.
        session.refresh(task)  # Récupère l'identifiant généré par la base.
    return task  # Retourne la tâche créée avec son identifiant.


@app.patch("/api/tasks/{task_id}", response_model=Task)  # Enregistre la route qui inverse l'état d'une tâche.
def toggle_task(task_id: int):  # Reçoit l'identifiant de la tâche à modifier.
    with Session(engine) as session:  # Ouvre une session pour rechercher et modifier la tâche.
        task = session.get(Task, task_id)  # Recherche la tâche à partir de son identifiant.
        if task is None:  # Vérifie que la tâche demandée existe.
            raise HTTPException(status_code=404, detail="Tâche introuvable")  # Signale que l'identifiant est inconnu.
        task.done = not task.done  # Bascule l'état terminé de la tâche.
        session.add(task)  # Prépare la tâche modifiée pour l'enregistrement.
        session.commit()  # Enregistre le nouvel état dans la base de données.
        session.refresh(task)  # Recharge la tâche modifiée avant de la retourner.
    return task  # Retourne la tâche dont l'état a été basculé.


@app.delete("/api/tasks/{task_id}")  # Enregistre la route de suppression d'une tâche.
def delete_task(task_id: int):  # Reçoit l'identifiant de la tâche à supprimer.
    with Session(engine) as session:  # Ouvre une session pour rechercher et supprimer la tâche.
        task = session.get(Task, task_id)  # Recherche la tâche à partir de son identifiant.
        if task is None:  # Vérifie que la tâche demandée existe.
            raise HTTPException(status_code=404, detail="Tâche introuvable")  # Signale que l'identifiant est inconnu.
        session.delete(task)  # Supprime la tâche de la session et de la base de données.
        session.commit()  # Enregistre définitivement la suppression.
    return {"message": "Tâche supprimée avec succès"}  # Confirme la suppression de la tâche.
