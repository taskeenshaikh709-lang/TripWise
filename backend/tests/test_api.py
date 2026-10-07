import os
import unittest


os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"

from app import create_app
from app.extensions import db


class TripWiseApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(TESTING=True)

    def setUp(self):
        with self.app.app_context():
            db.drop_all()
            db.create_all()
        self.client = self.app.test_client()
        response = self.client.post(
            "/api/auth/register",
            json={"name": "Test Traveler", "email": "traveler@example.com", "password": "safe-pass-123"},
        )
        self.assertEqual(response.status_code, 201)
        self.token = response.get_json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_health_and_auth_validation(self):
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()["message"], "TripWise API is running")
        duplicate = self.client.post(
            "/api/auth/register",
            json={"name": "Traveler", "email": "TRAVELER@example.com", "password": "safe-pass-123"},
        )
        self.assertEqual(duplicate.status_code, 409)
        bad_login = self.client.post(
            "/api/auth/login", json={"email": "traveler@example.com", "password": "wrong-password"}
        )
        self.assertEqual(bad_login.status_code, 401)
        good_login = self.client.post(
            "/api/auth/login",
            json={"email": "TRAVELER@example.com", "password": "safe-pass-123"},
        )
        self.assertEqual(good_login.status_code, 200)
        me = self.client.get("/api/auth/me", headers=self.headers)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.get_json()["user"]["email"], "traveler@example.com")

    def test_trip_budget_itinerary_expenses_and_export(self):
        payload = {
            "destination": "Jaipur",
            "start_location": "Delhi",
            "start_date": "2027-02-01",
            "end_date": "2027-02-03",
            "travelers": 2,
            "budget": 30000,
            "currency": "INR",
            "interests": ["Historical", "Culture"],
        }
        created = self.client.post("/api/trips", json=payload, headers=self.headers)
        self.assertEqual(created.status_code, 201, created.get_json())
        trip_id = created.get_json()["trip"]["id"]
        self.assertEqual(created.get_json()["trip"]["days"], 3)

        private = self.client.get(f"/api/trips/{trip_id}")
        self.assertEqual(private.status_code, 401)

        generated = self.client.post(f"/api/trips/{trip_id}/generate", headers=self.headers)
        self.assertEqual(generated.status_code, 200, generated.get_json())
        days = generated.get_json()["itinerary"]
        self.assertTrue(days)
        items = [item for day in days for item in day["items"]]
        self.assertTrue(all(item["start_time"] < item["end_time"] for item in items))
        self.assertEqual(len({item["place_id"] for item in items}), len(items))
        for day in days:
            for previous, following in zip(day["items"], day["items"][1:]):
                self.assertLessEqual(previous["end_time"], following["start_time"])
        recommendations = self.client.get(
            f"/api/trips/{trip_id}/recommendations", headers=self.headers
        ).get_json()["recommendations"]
        self.assertTrue(recommendations)
        self.assertGreaterEqual(recommendations[0]["score"], recommendations[-1]["score"])

        expense = self.client.post(
            f"/api/trips/{trip_id}/expenses",
            headers=self.headers,
            json={"category": "food", "description": "Lunch", "amount": 850, "date": "2027-02-01"},
        )
        self.assertEqual(expense.status_code, 201, expense.get_json())
        expense_id = expense.get_json()["expense"]["id"]
        budget = self.client.get(f"/api/trips/{trip_id}/budget", headers=self.headers).get_json()["budget"]
        self.assertEqual(budget["actual_total"], 850)
        self.assertEqual(budget["remaining"], 29150)

        edited = self.client.put(
            f"/api/trips/{trip_id}/expenses/{expense_id}",
            headers=self.headers,
            json={"amount": 900},
        )
        self.assertEqual(edited.status_code, 200, edited.get_json())
        self.assertEqual(edited.get_json()["expense"]["amount"], 900)

        pdf = self.client.get(f"/api/trips/{trip_id}/export.pdf", headers=self.headers)
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.data.startswith(b"%PDF"))

        removed = self.client.delete(
            f"/api/trips/{trip_id}/expenses/{expense_id}", headers=self.headers
        )
        self.assertEqual(removed.status_code, 200)
        refreshed_budget = self.client.get(
            f"/api/trips/{trip_id}/budget", headers=self.headers
        ).get_json()["budget"]
        self.assertEqual(refreshed_budget["actual_total"], 0)

        weather = self.client.get(f"/api/trips/{trip_id}/weather", headers=self.headers)
        self.assertEqual(weather.get_json()["status"], "unavailable")
        paris = self.client.post(
            "/api/trips",
            headers=self.headers,
            json={
                "destination": "Paris",
                "start_date": "2027-05-01",
                "end_date": "2027-05-02",
                "travelers": 1,
                "budget": 1000,
                "currency": "EUR",
            },
        ).get_json()["trip"]
        self.assertEqual(
            self.client.post(
                f"/api/trips/{paris['id']}/generate", headers=self.headers
            ).status_code,
            200,
        )
        paris_pdf = self.client.get(
            f"/api/trips/{paris['id']}/export.pdf", headers=self.headers
        )
        self.assertEqual(paris_pdf.status_code, 200)

    def test_hotel_currency_and_trip_validation(self):
        invalid = self.client.post(
            "/api/trips",
            headers=self.headers,
            json={
                "destination": "Paris",
                "start_date": "2027-05-01",
                "end_date": "2027-05-02",
                "travelers": 1,
                "budget": float("nan"),
            },
        )
        self.assertEqual(invalid.status_code, 400)
        trip = self.client.post(
            "/api/trips",
            headers=self.headers,
            json={
                "destination": "Paris",
                "start_date": "2027-05-01",
                "end_date": "2027-05-02",
                "travelers": 1,
                "budget": 1000,
                "currency": "EUR",
            },
        )
        trip_id = trip.get_json()["trip"]["id"]
        hotels = self.client.get(f"/api/trips/{trip_id}/hotels", headers=self.headers).get_json()["hotels"]
        self.assertTrue(hotels)
        self.assertEqual(hotels[0]["currency"], "EUR")
        selected = self.client.post(
            f"/api/trips/{trip_id}/hotels/{hotels[0]['id']}", headers=self.headers
        )
        self.assertEqual(selected.status_code, 200)
        selected_trip = selected.get_json()["trip"]
        accommodation = next(
            item for item in selected_trip["budget_summary"]["categories"]
            if item["name"] == "Accommodation"
        )
        self.assertEqual(accommodation["estimated"], hotels[0]["price_per_night"])
        refused_change = self.client.put(
            f"/api/trips/{trip_id}",
            headers=self.headers,
            json={"currency": "INR"},
        )
        self.assertEqual(refused_change.status_code, 400)
        removed = self.client.delete(
            f"/api/trips/{trip_id}/hotels", headers=self.headers
        )
        self.assertEqual(removed.status_code, 200)
        self.assertIsNone(removed.get_json()["trip"]["selected_hotel"])

    def test_long_trip_keeps_open_days_in_the_itinerary(self):
        trip = self.client.post(
            "/api/trips",
            headers=self.headers,
            json={
                "destination": "Paris",
                "start_date": "2027-05-01",
                "end_date": "2027-05-30",
                "travelers": 1,
                "budget": 100000,
                "currency": "EUR",
            },
        ).get_json()["trip"]
        response = self.client.post(
            f"/api/trips/{trip['id']}/generate", headers=self.headers
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        itinerary = response.get_json()["itinerary"]
        self.assertEqual(len(itinerary), 30)
        self.assertTrue(any(not day["items"] for day in itinerary))

    def test_trip_changes_clear_a_stale_itinerary(self):
        trip = self.client.post(
            "/api/trips",
            headers=self.headers,
            json={
                "destination": "Jaipur",
                "start_date": "2027-06-01",
                "end_date": "2027-06-03",
                "travelers": 1,
                "budget": 30000,
            },
        ).get_json()["trip"]
        generated = self.client.post(
            f"/api/trips/{trip['id']}/generate", headers=self.headers
        )
        self.assertEqual(generated.status_code, 200)
        update = self.client.put(
            f"/api/trips/{trip['id']}",
            headers=self.headers,
            json={"start_date": "2027-06-02", "end_date": "2027-06-04"},
        )
        self.assertEqual(update.status_code, 200, update.get_json())
        self.assertIn("fresh itinerary", update.get_json()["message"])
        current = self.client.get(
            f"/api/trips/{trip['id']}", headers=self.headers
        ).get_json()["trip"]
        self.assertEqual(current["itinerary"], [])

    def test_trip_crud_duplicate_and_owner_scoped_delete(self):
        trip = self.client.post(
            "/api/trips",
            headers=self.headers,
            json={
                "destination": "Jaipur",
                "start_date": "2027-07-01",
                "end_date": "2027-07-02",
                "travelers": 1,
                "budget": 12000,
            },
        ).get_json()["trip"]
        edited = self.client.put(
            f"/api/trips/{trip['id']}",
            headers=self.headers,
            json={"budget": 15000},
        )
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.get_json()["trip"]["budget"], 15000)

        duplicate = self.client.post(
            f"/api/trips/{trip['id']}/duplicate", headers=self.headers
        )
        self.assertEqual(duplicate.status_code, 201)
        duplicate_id = duplicate.get_json()["trip"]["id"]
        listed = self.client.get("/api/trips", headers=self.headers).get_json()["trips"]
        self.assertEqual(len(listed), 2)
        self.assertEqual(
            self.client.delete(f"/api/trips/{duplicate_id}", headers=self.headers).status_code,
            200,
        )
        self.assertEqual(
            self.client.delete(f"/api/trips/{trip['id']}", headers=self.headers).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(f"/api/trips/{trip['id']}", headers=self.headers).status_code,
            404,
        )

    def test_trip_access_is_scoped_to_owner(self):
        response = self.client.post(
            "/api/auth/register",
            json={"name": "Second Traveler", "email": "second@example.com", "password": "safe-pass-123"},
        )
        other_headers = {"Authorization": f"Bearer {response.get_json()['access_token']}"}
        trip = self.client.post(
            "/api/trips",
            headers=self.headers,
            json={
                "destination": "Paris",
                "start_date": "2027-05-01",
                "end_date": "2027-05-02",
                "travelers": 1,
                "budget": 1000,
                "interests": [],
            },
        )
        trip_id = trip.get_json()["trip"]["id"]
        self.assertEqual(self.client.get(f"/api/trips/{trip_id}", headers=other_headers).status_code, 404)


if __name__ == "__main__":
    unittest.main()
