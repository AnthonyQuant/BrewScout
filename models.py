from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import urllib.parse
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    cafes = db.relationship('Cafe', backref='submitter', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    replies = db.relationship('ReviewReply', backref='user', lazy=True)
    votes = db.relationship('ReviewVote', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class Cafe(db.Model):
    __tablename__ = 'cafes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    zip_code = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=False)
    google_maps_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=True)
    opening_hours = db.Column(db.String(100), nullable=False)
    price_range = db.Column(db.String(50), nullable=False)
    seating_capacity = db.Column(db.String(50), nullable=False)

    # Workability Rating Factors (0.0 - 10.0 scale)
    wifi_speed_mbps = db.Column(db.Integer, nullable=False, default=50)
    wifi_quality_score = db.Column(db.Float, nullable=False, default=8.0)
    power_outlet_score = db.Column(db.Float, nullable=False, default=7.0)
    noise_level_score = db.Column(db.Float, nullable=False, default=7.5)
    seating_comfort_score = db.Column(db.Float, nullable=False, default=8.0)
    affordability_score = db.Column(db.Float, nullable=False, default=7.0)
    opening_hours_score = db.Column(db.Float, nullable=False, default=8.0)

    # Student & Remote Operating Metrics
    has_backup_power = db.Column(db.Boolean, default=True, nullable=False)
    socket_accessibility = db.Column(db.String(100), default='Moderate Access', nullable=False)
    is_meeting_friendly = db.Column(db.Boolean, default=False, nullable=False)

    # Data Freshness & Verification System Fields
    last_verified_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    verification_status = db.Column(db.String(50), default='Recently Checked', nullable=False)
    wifi_last_tested_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Approval & Submitter Ownership
    is_approved = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    verification_reports = db.relationship('VerificationReport', backref='cafe', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='cafe', lazy=True, cascade='all, delete-orphan')

    def calculate_workability_score(self, custom_weights=None):
        weights = custom_weights or {
            'wifi': 0.25, 'outlets': 0.20, 'noise': 0.20,
            'seating': 0.15, 'affordability': 0.10, 'hours': 0.10
        }
        score = (
            (self.wifi_quality_score * weights.get('wifi', 0.25)) +
            (self.power_outlet_score * weights.get('outlets', 0.20)) +
            (self.noise_level_score * weights.get('noise', 0.20)) +
            (self.seating_comfort_score * weights.get('seating', 0.15)) +
            (self.affordability_score * weights.get('affordability', 0.10)) +
            (self.opening_hours_score * weights.get('hours', 0.10))
        )
        return round(score, 1)

    @property
    def average_user_rating(self):
        """Calculates dynamic average star rating from approved community reviews."""
        approved_reviews = [r for r in self.reviews if r.is_approved]
        if not approved_reviews:
            return None
        total = sum(r.rating for r in approved_reviews)
        return round(total / len(approved_reviews), 1)

    @property
    def dynamic_maps_url(self):
        if self.google_maps_url and self.google_maps_url.startswith('http'):
            return self.google_maps_url
        query = f"{self.name}, {self.address}"
        if self.zip_code:
            query += f" {self.zip_code}"
        return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query)}"

    @property
    def embed_maps_url(self):
        """Generates zero-cost Google Maps embed URL using output=embed parameter."""
        query = f"{self.name}, {self.address}"
        if self.zip_code:
            query += f" {self.zip_code}"
        return f"https://maps.google.com/maps?q={urllib.parse.quote(query)}&t=&z=15&ie=UTF8&iwloc=&output=embed"

    def __repr__(self):
        return f'<Cafe {self.name} - {self.location}>'


class VerificationReport(db.Model):
    __tablename__ = 'verification_reports'

    id = db.Column(db.Integer, primary_key=True)
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafes.id'), nullable=False)
    reporter_name = db.Column(db.String(100), nullable=True, default='Anonymous Contributor')
    wifi_speed_mbps = db.Column(db.Integer, nullable=True)
    price_range = db.Column(db.String(50), nullable=True)
    opening_hours = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_processed = db.Column(db.Boolean, default=False, nullable=False)


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    author_name = db.Column(db.String(100), nullable=False, default='Anonymous Coder')
    rating = db.Column(db.Integer, nullable=False, default=5)
    comment = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    replies = db.relationship('ReviewReply', backref='review', lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('ReviewVote', backref='review', lazy=True, cascade='all, delete-orphan')

    @property
    def approved_replies(self):
        return [reply for reply in self.replies if reply.is_approved]

    @property
    def likes_count(self):
        return sum(1 for vote in self.votes if vote.vote_type == 'like')

    @property
    def dislikes_count(self):
        return sum(1 for vote in self.votes if vote.vote_type == 'dislike')

    def __repr__(self):
        return f'<Review {self.rating} stars for Cafe #{self.cafe_id}>'


class ReviewReply(db.Model):
    __tablename__ = 'review_replies'

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    author_name = db.Column(db.String(100), nullable=False, default='Anonymous Contributor')
    comment = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<ReviewReply to Review #{self.review_id}>'


class ReviewVote(db.Model):
    __tablename__ = 'review_votes'

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint('review_id', 'user_id', name='unique_user_review_vote'),)