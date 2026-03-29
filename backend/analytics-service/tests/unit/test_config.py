from src.core.config import settings


def test_mongodb_url_property_maps_to_analytics_url():
    assert settings.MONGODB_URL == settings.ANALYTICS_MONGODB_URL
