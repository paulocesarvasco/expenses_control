import os

from sqlalchemy import create_engine, inspect, text

DEFAULT_PAYMENT_METHODS = [
    'Cartão de Crédito',
    'Cartão de Débito',
    'Dinheiro',
    'PIX',
    'Vale',
]


def _require_db_url() -> str:
    db_url = os.getenv("DB_URL", "").strip()
    if not db_url:
        raise RuntimeError("DB_URL environment variable is required")
    return db_url


def _has_payment_method_table(engine) -> bool:
    return 'payment_methods' in inspect(engine).get_table_names()


def _column_names(engine, table_name: str):
    return {column["name"] for column in inspect(engine).get_columns(table_name)}


def _seed_payment_methods(conn) -> None:
    for method_name in DEFAULT_PAYMENT_METHODS:
        conn.execute(
            text(
                """
                INSERT INTO payment_methods (payment_method_name)
                SELECT :method_name
                WHERE NOT EXISTS (
                    SELECT 1 FROM payment_methods WHERE payment_method_name = :method_name
                )
                """
            ),
            {"method_name": method_name},
        )


def _migrate_postgresql(engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS payment_methods (
                    payment_method_id SERIAL PRIMARY KEY,
                    payment_method_name VARCHAR(50) NOT NULL UNIQUE
                )
                """
            )
        )
        _seed_payment_methods(conn)

        conn.execute(text("ALTER TABLE shopping_trips ADD COLUMN IF NOT EXISTS payment_method_id INTEGER"))
        conn.execute(
            text(
                """
                UPDATE shopping_trips
                SET payment_method_id = pm.payment_method_id
                FROM payment_methods pm
                WHERE shopping_trips.payment_method = pm.payment_method_name
                  AND shopping_trips.payment_method_id IS NULL
                """
            )
        )
        conn.execute(
            text(
                """
                ALTER TABLE shopping_trips
                ADD CONSTRAINT shopping_trips_payment_method_id_fkey
                FOREIGN KEY (payment_method_id) REFERENCES payment_methods(payment_method_id)
                """
            )
        )
        conn.execute(text("ALTER TABLE shopping_trips DROP COLUMN IF EXISTS payment_method"))


def _migrate_sqlite(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS payment_methods (
                    payment_method_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_method_name VARCHAR(50) NOT NULL UNIQUE
                )
                """
            )
        )
        _seed_payment_methods(conn)
        conn.execute(
            text(
                """
                CREATE TABLE shopping_trips_new (
                    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_name VARCHAR(100) NOT NULL,
                    purchase_date DATE NOT NULL,
                    total_amount FLOAT,
                    payment_method_id INTEGER,
                    notes VARCHAR(150),
                    FOREIGN KEY(payment_method_id) REFERENCES payment_methods(payment_method_id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO shopping_trips_new
                    (trip_id, store_name, purchase_date, total_amount, payment_method_id, notes)
                SELECT
                    trip_id,
                    store_name,
                    purchase_date,
                    total_amount,
                    (
                        SELECT payment_method_id
                        FROM payment_methods
                        WHERE payment_method_name = shopping_trips.payment_method
                    ),
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

    shopping_trip_columns = _column_names(engine, "shopping_trips")
    if "payment_method_id" in shopping_trip_columns and _has_payment_method_table(engine):
        print('No migration needed: payment methods already normalized')
        return

    if "payment_method" not in shopping_trip_columns:
        raise RuntimeError('Column "payment_method" not found in "shopping_trips" table')

    if dialect == "postgresql":
        _migrate_postgresql(engine)
    elif dialect == "sqlite":
        _migrate_sqlite(engine)
    else:
        raise RuntimeError(f"Unsupported database dialect: {dialect}")

    print('Migration complete: shopping_trips.payment_method normalized into payment_methods')


if __name__ == "__main__":
    main()
