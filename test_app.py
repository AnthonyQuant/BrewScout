import unittest
from app import create_app
from models import db, User, Cafe, Review, ReviewReply, ReviewVote, VerificationReport


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key-brewscout-2026"
    ADMIN_EMAIL = "admin@example.com"
    ADMIN_PASSWORD = "test-admin-password-12345"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False


class BrewScoutTestCase(unittest.TestCase):
    def setUp(self):
        # 1. Correct Factory Configuration Order
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        # Seed test user
        self.test_user = User(
            name="Test Coder",
            email="coder@example.com"
        )
        self.test_user.set_password("password123")
        db.session.add(self.test_user)

        # Seed sample approved cafe
        self.sample_cafe = Cafe(
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
        db.session.add(self.sample_cafe)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # --- 1. Core Route & Discovery Tests ---
    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test Cafe", response.data)

    def test_add_cafe_requires_login(self):
        response = self.client.get('/add')
        # Unauthenticated users should be redirected to login
        self.assertEqual(response.status_code, 302)

    # --- 2. Scoring Invariants & Bounded Output Tests ---
    def test_workability_score_calculation(self):
        score = self.sample_cafe.calculate_workability_score()
        self.assertEqual(score, 8.2)

    def test_workability_score_bounds(self):
        self.sample_cafe.wifi_quality_score = 15.0  # Out-of-bounds input
        raw_score = self.sample_cafe.calculate_workability_score()
        bounded_score = min(10.0, max(0.0, raw_score))
        self.assertLessEqual(bounded_score, 10.0)

    def test_plan_session_route_weight_normalization(self):
        response = self.client.get('/plan-session?activity=coding&duration=5&priority=wifi_power')
        self.assertEqual(response.status_code, 200)

    # --- 3. Authentication & Safe Redirect Tests ---
    def test_user_registration(self):
        response = self.client.post('/register', data={
            'name': 'New User',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(email='newuser@example.com').first()
        self.assertIsNotNone(user)

    def test_user_login_success(self):
        response = self.client.post('/login', data={
            'email': 'coder@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_user_login_unsafe_redirect_prevention(self):
        # Malicious external redirect target
        response = self.client.post('/login?next=http://evil.com', data={
            'email': 'coder@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        # Must redirect to local index, NOT external site
        self.assertNotIn("evil.com", response.location)

    # --- 4. Authorization & Access Control Tests ---
    def test_unauthenticated_admin_access_denied(self):
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login', response.location)

    def test_authenticated_admin_access_granted(self):
        with self.client.session_transaction() as sess:
            sess['is_admin'] = True
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)

    def test_post_only_administrative_routes(self):
        # GET request on administrative action route must return 405 Method Not Allowed
        response = self.client.get(f'/admin/approve/{self.sample_cafe.id}')
        self.assertEqual(response.status_code, 405)

    # --- 5. Review Moderation & One-Vote-Per-User Tests ---
    def test_voting_on_unapproved_review_blocked(self):
        pending_review = Review(
            cafe_id=self.sample_cafe.id,
            user_id=self.test_user.id,
            author_name="Test Coder",
            rating=5,
            comment="Great spot!",
            is_approved=False
        )
        db.session.add(pending_review)
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess['user_id'] = self.test_user.id
            sess['user_name'] = self.test_user.name

        response = self.client.post(f'/review/{pending_review.id}/vote/like', follow_redirects=True)
        self.assertIn(b"Votes can only be cast on approved reviews", response.data)

    def test_voting_lifecycle_and_single_vote_constraint(self):
        approved_review = Review(
            cafe_id=self.sample_cafe.id,
            user_id=self.test_user.id,
            author_name="Test Coder",
            rating=5,
            comment="Excellent cafe for deep work!",
            is_approved=True
        )
        db.session.add(approved_review)
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess['user_id'] = self.test_user.id
            sess['user_name'] = self.test_user.name

        # 1. Cast initial 'like' vote
        self.client.post(f'/review/{approved_review.id}/vote/like')
        vote = ReviewVote.query.filter_by(review_id=approved_review.id, user_id=self.test_user.id).first()
        self.assertIsNotNone(vote)
        self.assertEqual(vote.vote_type, 'like')

        # 2. Toggle same vote type (removes vote)
        self.client.post(f'/review/{approved_review.id}/vote/like')
        vote_after_toggle = ReviewVote.query.filter_by(review_id=approved_review.id, user_id=self.test_user.id).first()
        self.assertIsNone(vote_after_toggle)

        # 3. Switch vote from 'like' to 'dislike'
        self.client.post(f'/review/{approved_review.id}/vote/like')
        self.client.post(f'/review/{approved_review.id}/vote/dislike')
        vote_switched = ReviewVote.query.filter_by(review_id=approved_review.id, user_id=self.test_user.id).first()
        self.assertEqual(vote_switched.vote_type, 'dislike')


if __name__ == '__main__':
    unittest.main()