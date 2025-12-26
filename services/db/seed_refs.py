import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from services.db.database import SessionLocal, engine, Base
from services.db.models import RefCiv, RefMap
# Ensure all models are imported so Base knows about them
import services.db.models 
from services.mappings import CIV_ID_TO_NAME, MAP_ID_TO_NAME

def seed_refs():
    db = SessionLocal()
    try:
        # Seed Civs
        print("Seeding RefCivs...")
        existing_civs = {c.civ_id: c for c in db.query(RefCiv).all()}
        count_c = 0
        for cid, cname in CIV_ID_TO_NAME.items():
            if cid not in existing_civs:
                db.add(RefCiv(civ_id=cid, civ_name=cname))
                count_c += 1
            else:
                # Update name if changed in mappings
                if existing_civs[cid].civ_name != cname:
                    existing_civs[cid].civ_name = cname
                    count_c += 1
        
        # Seed Maps
        print("Seeding RefMaps...")
        existing_maps = {m.map_name: m for m in db.query(RefMap).all()}
        count_m = 0
        for mid, mname in MAP_ID_TO_NAME.items():
            if mname and mname not in existing_maps:
                db.add(RefMap(map_name=mname))
                count_m += 1
        
        db.commit()
        print(f"Done. Added/Updated {count_c} civs, {count_m} maps.")
        
    except Exception as e:
        print(f"Error seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing DB Schema if needed...")
    Base.metadata.create_all(bind=engine)
    seed_refs()
