from typing import Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .models import Base, UserStream, UserCreatedEvent, UserUpdatedEvent, View
from .vector_clock import VectorClock

def main():
    # Database configuration
    DATABASE_URL = 'sqlite:///event_stream.db'  # Replace with your database URL

    # Create the SQLAlchemy engine
    engine = create_engine(DATABASE_URL, echo=True, future=True)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create a configured "Session" class
    Session = scoped_session(sessionmaker(bind=engine))

    # Create a Session
    session = Session()

    try:
        # Check if the UserStream already exists
        user_stream = session.query(UserStream).filter_by(name="user_stream").first()
        if not user_stream:
            # Create a new user stream
            user_stream = UserStream()
            session.add(user_stream)
            session.commit()
            print(f"Created UserStream with ID: {user_stream.id}")
        else:
            print(f"UserStream already exists with ID: {user_stream.id}")

        # Initialize vector clock
        vector_clock = VectorClock()

        # Create a user created event
        user_created = UserCreatedEvent(
            stream_id=user_stream.id,
            vector_clock=vector_clock.to_dict(),
            data={"username": "johndoe", "email": "john@example.com"}
        )
        session.add(user_created)
        vector_clock.increment(user_stream.id)

        # Create a user updated event
        user_updated = UserUpdatedEvent(
            stream_id=user_stream.id,
            vector_clock=vector_clock.to_dict(),
            data={"email": "john.doe@example.com"}
        )
        session.add(user_updated)
        vector_clock.increment(user_stream.id)

        # Commit events to the database
        session.commit()
        print("Events committed to the database.")

        # Update the view
        view = session.query(View).filter_by(stream_id=user_stream.id).first()
        if not view:
            view = View(stream_id=user_stream.id)
            session.add(view)
            session.commit()
            print("Created new View for the UserStream.")

        # Retrieve all events for the stream
        events = session.query(user_stream.events).all()[0]

        # Sort events using the complete sort_events method
        sorted_events = VectorClock.sort_events(events)

        # Apply events to the view
        for event in sorted_events:
            view.apply_event(event)

        # Commit the updated view
        session.commit()
        print("View updated with latest events.")

        # Display the current state
        print("Current View Snapshot:")
        print(view.snapshot)

    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")

    finally:
        # Close the session
        session.close()
