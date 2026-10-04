"""Idempotent seed of DEMO facilities. Not verified; not live availability."""
from .database import Base, SessionLocal, engine
from .models import Facility

DEMO = [
    ("Demo General Hospital (Kolkata)", "Hospital", "Kolkata", "Demo address, Kolkata", "000-000-0001", 22.5726, 88.3639, True, True, True),
    ("Demo Emergency Medical Center", "Emergency Medical Center", "Kolkata", "Demo address, Kolkata", "000-000-0002", 22.5448, 88.3426, True, False, False),
    ("Demo Ambulance Service", "Ambulance Service", "Kolkata", "Demo address, Kolkata", "000-000-0003", 22.5958, 88.2636, False, True, False),
    ("Demo Blood Bank", "Blood Bank", "Kolkata", "Demo address, Kolkata", "000-000-0004", 22.5675, 88.3700, False, False, True),
    ("Demo Community Clinic", "Clinic", "Kolkata", "Demo address, Kolkata", "000-000-0005", 22.5100, 88.3500, False, False, False),
]


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    added = 0
    for n, t, c, a, p, la, lo, e, am, b in DEMO:
        if not db.query(Facility).filter(Facility.name == n).first():
            db.add(Facility(name=n, type=t, city=c, address=a, phone=p, latitude=la, longitude=lo,
                            emergency_available=e, ambulance_available=am, blood_available=b, is_demo=True))
            added += 1
    db.commit(); db.close()
    print(f"Seeded {added} demo facilities (labelled is_demo=True).")


if __name__ == "__main__":
    run()
