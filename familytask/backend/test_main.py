import os
import tempfile
import unittest

from fastapi.testclient import TestClient

TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "familytask_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

import main


class AmbiguousFamilyLinkTests(unittest.TestCase):
    def setUp(self):
        main.SQLModel.metadata.drop_all(main.engine)
        main.SQLModel.metadata.create_all(main.engine)
        password_hash = main.hash_password("secret-pass")
        with main.Session(main.engine) as session:
            session.add_all([
                main.Member(
                    email="lea@example.com",
                    name="Léa",
                    lien="fille",
                    family_code="fam-test",
                    password_hash=password_hash,
                    is_admin=True,
                ),
                main.Member(
                    email="emma@example.com",
                    name="Emma",
                    lien="fille",
                    family_code="fam-test",
                    password_hash=password_hash,
                ),
            ])
            session.commit()

    def tearDown(self):
        main.SQLModel.metadata.drop_all(main.engine)
        if os.path.exists("test_familytask.db"):
            os.remove("test_familytask.db")

    def test_detects_ambiguous_female_link_in_raw_message(self):
        result = main.find_ambiguous_family_reference("fam-test", "Ajoute une tâche pour ma fille")
        self.assertEqual(result, "Il y a plusieurs filles (Léa, Emma). Pour qui ?")


class AssistantRouteTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop("AI_TOKEN", None)
        main.SQLModel.metadata.drop_all(main.engine)
        main.SQLModel.metadata.create_all(main.engine)
        password_hash = main.hash_password("secret-pass")
        with main.Session(main.engine) as session:
            session.add(
                main.Member(
                    email="assistant@example.com",
                    name="Alice",
                    lien="mère",
                    family_code="fam-test",
                    password_hash=password_hash,
                    is_admin=True,
                    token=main.hash_token("assistant-token"),
                )
            )
            session.commit()

    def tearDown(self):
        os.environ.pop("AI_TOKEN", None)
        main.SQLModel.metadata.drop_all(main.engine)
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_assistant_without_ai_token_returns_local_fallback(self):
        with TestClient(main.app) as client:
            response = client.post(
                "/api/assistant",
                json={"message": "Ajoute une tâche pour ranger la cuisine"},
                headers={"Authorization": "Bearer assistant-token"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("assistant", payload["message"].lower())


if __name__ == "__main__":
    unittest.main()
