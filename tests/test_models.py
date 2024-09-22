import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.gundb.models import Base, EventStream, Event, View, UserStream, UserEvent, UserCreatedEvent, UserUpdatedEvent
from src.gundb.site import Site
from src.gundb.vector_clock import VectorClock

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_event_stream_creation(db_session):
    user_stream = UserStream()
    db_session.add(user_stream)
    db_session.commit()

    assert user_stream.id is not None
    assert user_stream.name == "user_stream"
    assert user_stream.get_type() == UserEvent
    assert user_stream.latest_merged_event_counter == 0

def test_event_creation(db_session):
    user_stream = UserStream()
    db_session.add(user_stream)
    db_session.commit()

    site = Site()
    vector_clock = VectorClock.increment({}, site, str(user_stream.id))
    user_data = UserEvent(username="test_user", email="test@example.com", age=30)
    event = UserCreatedEvent(stream=user_stream, vector_clock=vector_clock, data=user_data)
    
    db_session.add(event)
    db_session.commit()

    assert event.id is not None
    assert event.stream_id == user_stream.id
    assert event.type == "UserCreatedEvent"
    assert event.data == {"username": "test_user", "email": "test@example.com", "age": 30}

def test_view_creation_and_update(db_session):
    user_stream = UserStream()
    db_session.add(user_stream)
    db_session.commit()

    site = Site()
    vector_clock = VectorClock.increment({}, site, str(user_stream.id))
    user_data = UserEvent(username="test_user", email="test@example.com", age=30)
    event = UserCreatedEvent(stream=user_stream, vector_clock=vector_clock, data=user_data)

    user_stream.apply_event(event, site)
    db_session.commit()

    assert user_stream.view is not None
    assert user_stream.view.snapshot == {"username": "test_user", "email": "test@example.com", "age": 30}
    assert user_stream.view.vector_clock == event.vector_clock
    assert user_stream.latest_merged_event_counter == 1

def test_multiple_events_and_sorting(db_session):
    user_stream = UserStream()
    db_session.add(user_stream)
    db_session.commit()

    site1 = Site()
    site2 = Site()

    # Create first event
    vc1 = VectorClock.increment({}, site1, str(user_stream.id))
    user_data1 = UserEvent(username="user1", email="user1@example.com", age=25)
    event1 = UserCreatedEvent(stream=user_stream, vector_clock=vc1, data=user_data1)

    # Create second event
    vc2 = VectorClock.increment(vc1, site2, str(user_stream.id))
    user_data2 = UserEvent(username="user1", email="updated@example.com", age=26)
    event2 = UserUpdatedEvent(stream=user_stream, vector_clock=vc2, data=user_data2)

    # Apply events in reverse order
    user_stream.update_with_events([event2, event1], site1)
    db_session.commit()

    assert user_stream.view.snapshot == {"username": "user1", "email": "updated@example.com", "age": 26}
    assert user_stream.view.vector_clock == event2.vector_clock
    assert user_stream.latest_merged_event_counter == 2

def test_event_stream_validation(db_session):
    user_stream = UserStream()
    
    valid_data = {"username": "valid_user", "email": "valid@example.com", "age": 30}
    invalid_data = {"username": "invalid_user", "email": "invalid@example.com"}  # Missing 'age'

    assert user_stream.validate_data(valid_data)
    
    with pytest.raises(ValueError):
        user_stream.validate_data(invalid_data)

def test_get_schema(db_session):
    user_stream = UserStream()
    schema = user_stream.get_schema()

    assert "properties" in schema
    assert "username" in schema["properties"]
    assert "email" in schema["properties"]
    assert "age" in schema["properties"]

def test_latest_merged_event_counter(db_session):
    user_stream = UserStream()
    db_session.add(user_stream)
    db_session.commit()

    site = Site()

    # Create and apply three events
    for i in range(3):
        vector_clock = VectorClock.increment({}, site, str(user_stream.id))
        user_data = UserEvent(username=f"user{i}", email=f"user{i}@example.com", age=25+i)
        event = UserCreatedEvent(stream=user_stream, vector_clock=vector_clock, data=user_data)
        user_stream.apply_event(event, site)

    db_session.commit()

    assert user_stream.latest_merged_event_counter == 3

    # Apply an event with a higher position
    vector_clock = VectorClock.increment({}, site, str(user_stream.id))
    user_data = UserEvent(username="user5", email="user5@example.com", age=30)
    event = UserCreatedEvent(stream=user_stream, vector_clock=vector_clock, data=user_data)
    event.position = 5  # Manually set a higher position
    user_stream.apply_event(event, site)

    db_session.commit()

    assert user_stream.latest_merged_event_counter == 5

if __name__ == "__main__":
    pytest.main()
