"""
seed.py — Seed extension officers. Run from backend/: python seed.py
"""

import asyncio
import sys

sys.path.insert(0, ".")

from app.database import init_db, get_db
from app.models.officer import ExtensionOfficer, OfficerSpecialization

OFFICERS = [
    {
        "name": "James Mwangi",
        "phone_number": "254712345001",
        "county": "Nakuru",
        "specialization": OfficerSpecialization.CROPS,
        "notes": "Maize and wheat specialist. Mon-Fri 8am-5pm. Kikuyu & Swahili.",
    },
    {
        "name": "Grace Achieng",
        "phone_number": "254712345002",
        "county": "Kisumu",
        "specialization": OfficerSpecialization.LIVESTOCK,
        "notes": "Dairy cattle and poultry expert. Covers Kisumu and Siaya. Speaks Luo.",
    },
    {
        "name": "Peter Mutua",
        "phone_number": "254712345003",
        "county": "Machakos",
        "specialization": OfficerSpecialization.AGROFORESTRY,
        "notes": "Dryland farming and agroforestry in ASAL regions.",
    },
    {
        "name": "Faith Wanjiru",
        "phone_number": "254712345004",
        "county": "Meru",
        "specialization": OfficerSpecialization.HORTICULTURE,
        "notes": "French beans, tomatoes, avocado. Export-grade certification experience.",
    },
    {
        "name": "Samuel Koech",
        "phone_number": "254712345005",
        "county": "Uasin Gishu",
        "specialization": OfficerSpecialization.CROPS,
        "notes": "Wheat and maize in the Rift Valley. Large-scale and smallholder ops.",
    },
    {
        "name": "Agnes Njeri",
        "phone_number": "254712345006",
        "county": "Kiambu",
        "specialization": OfficerSpecialization.GENERAL,
        "notes": "Peri-urban farming around Nairobi. Handles escalations.",
    },
    {
        "name": "Daniel Otieno",
        "phone_number": "254712345007",
        "county": "Homa Bay",
        "specialization": OfficerSpecialization.LIVESTOCK,
        "notes": "Goats, poultry, and fish farming along Lake Victoria basin.",
    },
    {
        "name": "Miriam Chebet",
        "phone_number": "254712345008",
        "county": "Nandi",
        "specialization": OfficerSpecialization.CROPS,
        "notes": "Tea and pyrethrum in the highlands. Dairy fodder crops.",
    },
]


async def seed():
    await init_db()
    async with get_db() as db:
        for data in OFFICERS:
            db.add(ExtensionOfficer(**data))
        await db.commit()
    print(f"✅ Seeded {len(OFFICERS)} extension officers.")


if __name__ == "__main__":
    asyncio.run(seed())
