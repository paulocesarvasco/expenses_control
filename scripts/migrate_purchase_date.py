import os

from sqlalchemy import create_engine, inspect, text


def _require_db_url() -> str:
    db_url = os.getenv("DB_URL", "").strip()
    if not db_url:
        raise RuntimeError("DB_URL environment variable is required")
    return db_url


def _column_type_name(engine) -> str:
    inspector = inspect(engine)
    columns = inspector.get_columns("shopping_trips")
    for column in columns:
        if column["name"] == "purchase_date":
            return str(column["type"]).upper()
    raise RuntimeError('Column "purchase_date" not found in "shopping_trips" table')


def _migrate_postgresql(engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                ALTER TABLE shopping_trips
                ALTER COLUMN purchase_date
                TYPE DATE
                USING purchase_date::date
                """
            )
        )


def _migrate_sqlite(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.execute(
            text(
                """
                CREATE TABLE shopping_trips_new (
                    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_name VARCHAR(100) NOT NULL,
                    purchase_date DATE NOT NULL,
                    total_amount FLOAT,
                    payment_method VARCHAR(50),
                    notes VARCHAR(150)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO shopping_trips_new
                    (trip_id, store_name, purchase_date, total_amount, payment_method, notes)
                SELECT
                    trip_id,
                    store_name,
                    date(purchase_date),
                    total_amount,
                    payment_method,
                    notes
                FROM shopping_trips
                """
            )
        )
        conn.execute(text("DROP TABLE shopping_trips"))
        conn.execute(text("ALTER TABLE shopping_trips_new RENAME TO shopping_trips"))
        conn.execute(text("PRAGMA foreign_keys=ON"))


def main() -> None:
    db_url = _require_db_url()
    engine = create_engine(db_url, echo=False)
    dialect = engine.dialect.name
    current_type = _column_type_name(engine)

    if "DATE" in current_type:
        print('No migration needed: "purchase_date" is already DATE-like')
        return

    if dialect == "postgresql":
        _migrate_postgresql(engine)
    elif dialect == "sqlite":
        _migrate_sqlite(engine)
    else:
        raise RuntimeError(f"Unsupported database dialect: {dialect}")

    print('Migration complete: "shopping_trips.purchase_date" converted to DATE')


if __name__ == "__main__":
    main()
