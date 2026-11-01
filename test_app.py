import unittest
from app import create_app
from models import db, Cafe

class BrewScoutTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            sample_cafe = Cafe(
                name="Test Cafe",
                location="Downtown",
                zip_code="90001",
                address="123 Test Street",
                google_maps_url="https://maps.google.com/?q=Test+Cafe",
                opening_hours="08:00 AM - 08:00 PM",
                price_range="Moderate",
                seating_capacity="30 seats",
                wifi_speed_mbps=100,
                wifi_quality_score=9.0,
                power_outlet_score=8.0,
                noise_level_score=8.0,
                seating_comfort_score=8.0,
                affordability_score=7.0,
                opening_hours_score=8.0,
                is_approved=True
            )
            db.session.add(sample_cafe)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test Cafe", response.data)

    def test_workability_score_calculation(self):
        with self.app.app_context():
            cafe = db.session.query(Cafe).filter_by(name="Test Cafe").first()
            score = cafe.calculate_workability_score()
            self.assertEqual(score, 8.2)

    def test_plan_session_route(self):
        response = self.client.get('/plan-session?activity=coding')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Recommended Locations", response.data)

    def test_add_cafe_form_render(self):
        response = self.client.get('/add')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()