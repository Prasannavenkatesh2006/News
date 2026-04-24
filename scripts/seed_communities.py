"""
Seed the database with default communities.
Run this after database tables are created.
"""
from anip.shared.database import get_db_session
from anip.shared.models.social import Community

DEFAULT_COMMUNITIES = [
    {"name": "Technology & AI", "slug": "technology", "description": "Artificial intelligence, software, hardware, and tech industry news."},
    {"name": "Economy & Finance", "slug": "economy", "description": "Markets, inflation, trade, and global economic developments."},
    {"name": "Politics & Government", "slug": "politics", "description": "Elections, policy, legislation, and geopolitics."},
    {"name": "Climate & Environment", "slug": "climate", "description": "Climate change, sustainability, and environmental science."},
    {"name": "Health & Medicine", "slug": "health", "description": "Medical research, public health, and healthcare industry."},
    {"name": "Natural Disasters", "slug": "natural-disasters", "description": "Earthquakes, floods, hurricanes, and emergency response."},
    {"name": "Science & Space", "slug": "science", "description": "Space exploration, physics, biology, and scientific discoveries."},
    {"name": "World News", "slug": "world", "description": "International affairs and breaking global news."},
]


def seed_communities():
    """Insert default communities if they don't exist."""
    with get_db_session() as db:
        for comm_data in DEFAULT_COMMUNITIES:
            existing = db.query(Community).filter(Community.slug == comm_data["slug"]).first()
            if not existing:
                community = Community(**comm_data)
                db.add(community)
                print(f"  [+] Created community: {comm_data['name']}")
            else:
                print(f"  [-] Community already exists: {comm_data['name']}")
        db.commit()
    print("Community seeding complete!")


if __name__ == "__main__":
    seed_communities()
