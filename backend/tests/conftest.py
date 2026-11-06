import os
os.environ['DATABASE_URL'] = 'sqlite://'

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_db
from app.main import app, buckets
from app.models import School, User, Subject
from app.security import passwords


@pytest.fixture
def context():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    def override():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override
    buckets.clear()
    with factory() as db:
        a, b = School(name='School A'), School(name='School B')
        db.add_all([a, b])
        db.flush()
        for name, role, school in [('admin', 'admin', a), ('teacher', 'teacher', a), ('student', 'student', a),
                                   ('peer', 'student', a), ('outsider', 'admin', b)]:
            db.add(User(name=name, email=f'{name}@test.in', role=role, school_id=school.id, password_hash=passwords.hash('TestPassword!2026')))
        db.add(Subject(name='Science', school_id=a.id))
        db.commit()
    clients = []
    def login(name):
        client = TestClient(app)
        result = client.post('/api/auth/login', json={'email': f'{name}@test.in', 'password': 'TestPassword!2026'})
        assert result.status_code == 200, result.text
        client.headers['x-csrf-token'] = result.json()['csrf_token']
        clients.append(client)
        return client
    yield login, factory
    for client in clients:
        client.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()
