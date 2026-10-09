from sqlalchemy import create_engine, text
from core.config import settings

engine = create_engine(settings.TEST_DATABASE_URL)

with engine.connect() as connection:
    print("DATABASE:")
    print(connection.execute(text("SELECT current_database()")).scalar())

    print("\nALEMBIC VERSION:")
    try:
        result = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).fetchall()
        print(result)
    except Exception as e:
        print("Error:", e)

    print("\nPRODUCTION BATCH TABLE:")
    print(
        connection.execute(
            text("SELECT to_regclass('public.production_batches')")
        ).scalar()
    )

    print("\nALL REQUIRED TABLES:")

    tables = [
        "users",
        "auth_tokens",
        "plants",
        "production_lines",
        "products",
        "raw_materials",
        "material_transactions",
        "boms",
        "bom_items",
        "machines",
        "production_orders",
        "production_batches",
    ]

    for table in tables:
        result = connection.execute(
            text(
                "SELECT to_regclass(:table_name)"
            ),
            {"table_name": f"public.{table}"},
        ).scalar()

        print(f"{table}: {result}")