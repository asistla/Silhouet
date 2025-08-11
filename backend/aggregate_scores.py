# backend/aggregate_scores.py
import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from shared_config.silhouet_config import PERSONALITY_KEYS

# --- Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Database Connection ---
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logging.info("Database engine created successfully.")
except Exception as e:
    logging.error(f"Failed to create database engine: {e}")
    exit(1)

# --- Aggregation Logic ---

def get_average_score_columns(keys, source_alias="source"):
    """Generates SQL expressions for averaging personality scores."""
    return [f"AVG({source_alias}.avg_{key}_score) AS avg_{key}_score" for key in keys]

def get_insert_columns(keys):
    """Generates column names for the INSERT statement."""
    return ["geo_level", "geo_identifier", "total_entities_contributing"] + [f"avg_{key}_score" for key in keys]

def get_update_setters(keys):
    """Generates SET expressions for the ON CONFLICT UPDATE clause."""
    setters = ["total_entities_contributing = EXCLUDED.total_entities_contributing"]
    setters.extend([f"avg_{key}_score = EXCLUDED.avg_{key}_score" for key in keys])
    return ", ".join(setters)

def aggregate_level(db, geo_level, source_level, source_table, source_geo_col):
    """
    A generic function to aggregate scores from a source level to a target geo level.
    """
    logging.info(f"Aggregating '{geo_level}' scores from '{source_level}' in table '{source_table}'.")

    avg_score_cols = get_average_score_columns(PERSONALITY_KEYS, "s")
    insert_cols = get_insert_columns(PERSONALITY_KEYS)
    update_setters = get_update_setters(PERSONALITY_KEYS)

    count_expression = "COUNT(s.user_id)" if source_table == 'users' else f"SUM(s.total_entities_contributing)"

    query = text(f"""
        INSERT INTO aggregated_geo_scores ({', '.join(insert_cols)})
        SELECT
            '{geo_level}' AS geo_level,
            s.{source_geo_col} AS geo_identifier,
            {count_expression} AS total_entities_contributing,
            {', '.join(avg_score_cols)}
        FROM {source_table} s
        WHERE s.{source_geo_col} IS NOT NULL
        GROUP BY s.{source_geo_col}
        ON CONFLICT (geo_level, geo_identifier) DO UPDATE
        SET {update_setters},
            last_updated_at = NOW();
    """)

    try:
        result = db.execute(query)
        db.commit()
        logging.info(f"Successfully aggregated '{geo_level}'. {result.rowcount} rows affected.")
    except SQLAlchemyError as e:
        logging.error(f"Error during aggregation for '{geo_level}'. Details: {e}")
        db.rollback()

def aggregate_global(db):
    """Aggregates all country-level scores into a single 'global' score."""
    logging.info("Aggregating 'global' scores from 'country' level.")

    avg_score_cols = get_average_score_columns(PERSONALITY_KEYS, "s")
    insert_cols = get_insert_columns(PERSONALITY_KEYS)
    update_setters = get_update_setters(PERSONALITY_KEYS)

    query = text(f"""
        INSERT INTO aggregated_geo_scores ({', '.join(insert_cols)})
        SELECT
            'global' AS geo_level,
            'global' AS geo_identifier,
            SUM(s.total_entities_contributing) AS total_entities_contributing,
            {', '.join(avg_score_cols)}
        FROM aggregated_geo_scores s
        WHERE s.geo_level = 'country'
        ON CONFLICT (geo_level, geo_identifier) DO UPDATE
        SET {update_setters},
            last_updated_at = NOW();
    """)
    try:
        result = db.execute(query)
        db.commit()
        logging.info(f"Successfully aggregated 'global' scores. {result.rowcount} rows affected.")
    except SQLAlchemyError as e:
        logging.error(f"Error during global aggregation. Details: {e}")
        db.rollback()

def main():
    """Main function to run a specific aggregation based on command-line argument."""
    if len(sys.argv) < 2:
        logging.error("No aggregation level specified. Usage: python aggregate_scores.py [level]")
        sys.exit(1)

    level = sys.argv[1]
    logging.info(f"Received request to aggregate level: {level}")

    db = SessionLocal()
    if not db:
        logging.error("Failed to create database session.")
        return

    try:
        if level == "pincode":
            aggregate_level(db, 'pincode', 'user', 'users', 'pincode')
        elif level == "city":
            aggregate_level(db, 'city', 'pincode', 'aggregated_geo_scores', 'geo_identifier')
        elif level == "district":
            aggregate_level(db, 'district', 'city', 'aggregated_geo_scores', 'geo_identifier')
        elif level == "state":
            aggregate_level(db, 'state', 'district', 'aggregated_geo_scores', 'geo_identifier')
        elif level == "country":
            aggregate_level(db, 'country', 'state', 'aggregated_geo_scores', 'geo_identifier')
        elif level == "global":
            aggregate_global(db)
        else:
            logging.error(f"Unknown aggregation level: {level}")
    finally:
        db.close()
        logging.info(f"Finished aggregation for level: {level}. Database session closed.")

if __name__ == "__main__":
    main()