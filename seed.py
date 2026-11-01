from datetime import datetime
from sqlalchemy.exc import OperationalError

from app import app
from models import db, Cafe, User

sample_cafes = [
    {
        "name": "Aura Coffee Roasters",
        "location": "Downtown Central",
        "zip_code": "90001",
        "address": "12 Commercial Avenue, Downtown",
        "google_maps_url": "https://maps.google.com/?q=Aura+Coffee+Roasters",
        "img_url": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb",
        "opening_hours": "07:00 AM - 09:00 PM",
        "price_range": "Moderate",
        "seating_capacity": "Spacious Lounge (60+ seats)",
        "has_backup_power": True,
        "socket_accessibility": "Abundant At Every Table",
        "is_meeting_friendly": False,
        "wifi_speed_mbps": 120,
        "wifi_quality_score": 9.5,
        "power_outlet_score": 9.0,
        "noise_level_score": 7.5,
        "seating_comfort_score": 8.5,
        "affordability_score": 7.0,
        "opening_hours_score": 8.5,
        "is_approved": True,
        "last_verified_date": datetime.utcnow(),
        "verification_status": "Recently Checked",
        "wifi_last_tested_date": datetime.utcnow()
    },
    {
        "name": "The Daily Grind & Code",
        "location": "Innovation Hub",
        "zip_code": "90002",
        "address": "45 Tech Boulevard, Suite 100",
        "google_maps_url": "https://maps.google.com/?q=The+Daily+Grind+and+Code",
        "img_url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24",
        "opening_hours": "06:30 AM - 11:00 PM",
        "price_range": "Budget-friendly",
        "seating_capacity": "Dedicated Quiet Study (40 seats)",
        "has_backup_power": True,
        "socket_accessibility": "Abundant At Every Table",
        "is_meeting_friendly": True,
        "wifi_speed_mbps": 200,
        "wifi_quality_score": 9.8,
        "power_outlet_score": 9.5,
        "noise_level_score": 9.0,
        "seating_comfort_score": 9.0,
        "affordability_score": 8.5,
        "opening_hours_score": 9.5,
        "is_approved": True,
        "last_verified_date": datetime.utcnow(),
        "verification_status": "Recently Checked",
        "wifi_last_tested_date": datetime.utcnow()
    },
    {
        "name": "Artisan Beans & Study Nook",
        "location": "University District",
        "zip_code": "90003",
        "address": "8 Academic Way, Campus Gate",
        "google_maps_url": "https://maps.google.com/?q=Artisan+Beans+Study+Nook",
        "img_url": "https://images.unsplash.com/photo-1521017432531-fbd92d768814",
        "opening_hours": "08:00 AM - 08:00 PM",
        "price_range": "Budget-friendly",
        "seating_capacity": "Medium Bistro (30 seats)",
        "has_backup_power": False,
        "socket_accessibility": "Moderate Access",
        "is_meeting_friendly": False,
        "wifi_speed_mbps": 85,
        "wifi_quality_score": 8.5,
        "power_outlet_score": 8.0,
        "noise_level_score": 8.5,
        "seating_comfort_score": 8.0,
        "affordability_score": 9.0,
        "opening_hours_score": 7.5,
        "is_approved": True,
        "last_verified_date": datetime.utcnow(),
        "verification_status": "Recently Checked",
        "wifi_last_tested_date": datetime.utcnow()
    },
    {
        "name": "Velvet Microfoam Lounge",
        "location": "West End Mall",
        "zip_code": "90004",
        "address": "102 Westside Plaza",
        "google_maps_url": "https://maps.google.com/?q=Velvet+Microfoam+Lounge",
        "img_url": "https://images.unsplash.com/photo-1442512595331-e89e73853f31",
        "opening_hours": "09:00 AM - 06:00 PM",
        "price_range": "Flexible",
        "seating_capacity": "Small Cafe (20 seats)",
        "has_backup_power": False,
        "socket_accessibility": "Limited Sockets",
        "is_meeting_friendly": False,
        "wifi_speed_mbps": 35,
        "wifi_quality_score": 6.5,
        "power_outlet_score": 5.0,
        "noise_level_score": 5.5,
        "seating_comfort_score": 7.5,
        "affordability_score": 5.5,
        "opening_hours_score": 6.0,
        "is_approved": True,
        "last_verified_date": datetime.utcnow(),
        "verification_status": "Recently Checked",
        "wifi_last_tested_date": datetime.utcnow()
    },
    {
        "name": "The Quiet Corner Workspace",
        "location": "Library Row",
        "zip_code": "90005",
        "address": "3 Scholarly Path",
        "google_maps_url": "https://maps.google.com/?q=The+Quiet+Corner+Workspace",
        "img_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4",
        "opening_hours": "07:00 AM - 10:00 PM",
        "price_range": "Moderate",
        "seating_capacity": "Ergonomic Silent Zone (50 seats)",
        "has_backup_power": True,
        "socket_accessibility": "Abundant At Every Table",
        "is_meeting_friendly": True,
        "wifi_speed_mbps": 150,
        "wifi_quality_score": 9.2,
        "power_outlet_score": 9.2,
        "noise_level_score": 9.8,
        "seating_comfort_score": 9.5,
        "affordability_score": 7.5,
        "opening_hours_score": 9.0,
        "is_approved": True,
        "last_verified_date": datetime.utcnow(),
        "verification_status": "Recently Checked",
        "wifi_last_tested_date": datetime.utcnow()
    }
]


def seed_database():
    with app.app_context():
        print(f"Using database: {db.engine.url.database}")
        try:
            # Drop old schema and rebuild all tables cleanly
            db.drop_all()
            db.create_all()

            db.session.add_all([Cafe(**data) for data in sample_cafes])
            db.session.commit()
        except OperationalError as exc:
            db.session.rollback()
            raise SystemExit(
                f"Database error while seeding: {exc.orig}"
            ) from exc

        print(f"Successfully re-seeded {len(sample_cafes)} benchmark cafes with updated verification fields into BrewScout database.")


if __name__ == '__main__':
    seed_database()