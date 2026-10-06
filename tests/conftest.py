import pytest
from app.db.database import db
from app.db.seed_data import reset_database
from app.tools.registry import tool_registry

@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Ensure database is reset and seeded with clean data before every test."""
    reset_database()
    yield

@pytest.fixture(autouse=True)
def reset_simulation_flags():
    """Reset simulated API failure flag before each test."""
    tool_registry.simulate_order_api_down = False
    yield
    tool_registry.simulate_order_api_down = False
