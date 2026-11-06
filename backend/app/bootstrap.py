"""Create the initial school administrator without shipping production default credentials."""
import argparse
import getpass
from sqlalchemy import select
from .db import SessionLocal
from .models import School, User, Subject
from .security import passwords


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--school', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--email', required=True)
    args = parser.parse_args()
    password = getpass.getpass('Administrator password (12+ characters): ')
    if len(password) < 12 or password != getpass.getpass('Repeat password: '):
        raise SystemExit('Passwords must match and contain at least 12 characters')
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == args.email.strip().lower())):
            raise SystemExit('Account already exists')
        school = School(name=args.school)
        db.add(school)
        db.flush()
        db.add(User(school_id=school.id, name=args.name, email=args.email.strip().lower(), role='admin', password_hash=passwords.hash(password)))
        for name in ['Science', 'Mathematics', 'English', 'Hindi']:
            db.add(Subject(school_id=school.id, name=name))
        db.commit()
    print('School administrator created.')


if __name__ == '__main__':
    main()
