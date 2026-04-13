import os
import tempfile
import unittest

from sqlalchemy import create_engine

from app import create_app
from app.models import Base


class ApiBaselineTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_expenses.db")
        self.db_url = f"sqlite:///{self.db_path}"

        self.previous_db_url = os.environ.get("DB_URL")
        os.environ["DB_URL"] = self.db_url

        engine = create_engine(self.db_url, echo=False)
        Base.metadata.create_all(engine)
        engine.dispose()

        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        if self.previous_db_url is None:
            os.environ.pop("DB_URL", None)
        else:
            os.environ["DB_URL"] = self.previous_db_url
        self.temp_dir.cleanup()

    def _register_category(self, category_name="Mercearia"):
        return self.client.post(
            "/v1/category/register",
            json={"category_name": category_name},
        )

    def _register_product(self, product_name="Arroz", category_name="Mercearia"):
        category_response = self._register_category(category_name=category_name)
        category_payload = category_response.get_json()
        category_id = category_payload["category_id"]

        return self.client.post(
            "/v1/product/register",
            json={
                "product_name": product_name,
                "category_id": category_id,
            },
        )

    def _register_purchase(self):
        self._register_product(product_name="Arroz")
        response = self.client.post(
            "/v1/purchase/save",
            json={
                "store_name": "Mercado Central",
                "purchase_date": "2026-04-10",
                "payment_method": "PIX",
                "items": [
                    {
                        "product_name": "Arroz",
                        "quantity": 2,
                        "price": 20.0,
                        "brand": "Marca A",
                    }
                ],
            },
        )
        return response

    def test_register_category(self):
        response = self._register_category("Higiene")
        payload = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["message"], "Category registered successfully")
        self.assertEqual(payload["category_name"], "Higiene")
        self.assertIn("category_id", payload)

    def test_register_product(self):
        response = self._register_product(
            product_name="Sabonete",
            category_name="Higiene",
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["message"], "Product registered successfully")
        self.assertEqual(payload["product_name"], "Sabonete")
        self.assertIn("product_id", payload)

    def test_save_purchase(self):
        response = self._register_purchase()
        payload = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["message"], "Purchase saved successfully")
        self.assertIn("trip_id", payload)

    def test_search_purchases_returns_html(self):
        self._register_purchase()
        response = self.client.get(
            "/v1/purchase/search?start=2026-04-01&end=2026-04-30"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Mercado Central", response.data)

    def test_search_purchases_returns_json_with_format_selector(self):
        self._register_purchase()
        response = self.client.get(
            "/v1/purchase/search?start=2026-04-01&end=2026-04-30&format=json"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(payload, list)
        self.assertGreaterEqual(len(payload), 1)
        self.assertEqual(payload[0]["store_name"], "Mercado Central")

    def test_update_purchase(self):
        create_response = self._register_purchase()
        trip_id = create_response.get_json()["trip_id"]

        update_response = self.client.patch(
            f"/v1/purchase/{trip_id}",
            json={
                "store_name": "Atacadao",
                "purchase_date": "2026-04-11",
                "payment_method": "Dinheiro",
            },
        )
        payload = update_response.get_json()

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(payload["trip_id"], trip_id)
        self.assertEqual(payload["store_name"], "Atacadao")
        self.assertEqual(payload["payment_method"], "Dinheiro")

    def test_update_purchase_item(self):
        create_response = self._register_purchase()
        trip_id = create_response.get_json()["trip_id"]

        items_response = self.client.get(f"/v1/purchase/{trip_id}/items")
        item_id = items_response.get_json()[0]["item_id"]

        update_response = self.client.patch(
            f"/v1/purchase/item/{item_id}",
            json={
                "brand": "Marca B",
                "quantity": 4,
                "total_price": 44.0,
            },
        )
        payload = update_response.get_json()

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(payload["item_id"], item_id)
        self.assertEqual(payload["brand"], "Marca B")
        self.assertEqual(payload["quantity"], 4.0)
        self.assertEqual(payload["total_price"], 44.0)

    def test_unexpected_error_returns_controlled_500_response(self):
        self.app.add_url_rule(
            "/v1/test-error",
            endpoint="test_error",
            view_func=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        response = self.client.get("/v1/test-error?format=json")
        payload = response.get_json()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(payload["error"]["message"], "Internal server error")


if __name__ == "__main__":
    unittest.main()
