#!/usr/bin/env python3
"""
Database Migration: Convert Chinese field values to English
Date: 2025-10-06
Description: This migration updates all Chinese risk levels, suggested actions, and sensitivity levels to English equivalents
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from config import settings
from utils.logger import setup_logger

logger = setup_logger()

# Field value mappings
RISK_LEVEL_MAPPING = {
    '无风险': 'no_risk',
    '低风险': 'low_risk',
    '中风险': 'medium_risk',
    '高风险': 'high_risk'
}

ACTION_MAPPING = {
    '通过': 'pass',
    '拒答': 'reject',
    '代答': 'replace',
    '阻断': 'block',
    '放行': 'allow'
}

SENSITIVITY_MAPPING = {
    '高': 'high',
    '中': 'medium',
    '低': 'low'
}

DATA_RISK_LEVEL_MAPPING = {
    '低': 'low',
    '中': 'medium',
    '高': 'high'
}

def migrate_detection_results(session):
    """Migrate detection_results table"""
    logger.info("Migrating detection_results table...")

    # Update risk levels
    for cn, en in RISK_LEVEL_MAPPING.items():
        # Security risk level
        result = session.execute(
            text("UPDATE detection_results SET security_risk_level = :en WHERE security_risk_level = :cn"),
            {"en": en, "cn": cn}
        )
        logger.info(f"Updated {result.rowcount} rows: security_risk_level '{cn}' -> '{en}'")

        # Compliance risk level
        result = session.execute(
            text("UPDATE detection_results SET compliance_risk_level = :en WHERE compliance_risk_level = :cn"),
            {"en": en, "cn": cn}
        )
        logger.info(f"Updated {result.rowcount} rows: compliance_risk_level '{cn}' -> '{en}'")

        # Data risk level
        result = session.execute(
            text("UPDATE detection_results SET data_risk_level = :en WHERE data_risk_level = :cn"),
            {"en": en, "cn": cn}
        )
        logger.info(f"Updated {result.rowcount} rows: data_risk_level '{cn}' -> '{en}'")

    # Update suggested actions
    for cn, en in ACTION_MAPPING.items():
        result = session.execute(
            text("UPDATE detection_results SET suggest_action = :en WHERE suggest_action = :cn"),
            {"en": en, "cn": cn}
        )
        logger.info(f"Updated {result.rowcount} rows: suggest_action '{cn}' -> '{en}'")

    # Update sensitivity levels
    for cn, en in SENSITIVITY_MAPPING.items():
        result = session.execute(
            text("UPDATE detection_results SET sensitivity_level = :en WHERE sensitivity_level = :cn"),
            {"en": en, "cn": cn}
        )
        logger.info(f"Updated {result.rowcount} rows: sensitivity_level '{cn}' -> '{en}'")

    session.commit()
    logger.info("detection_results migration completed")

def migrate_response_templates(session):
    """Migrate response_templates table"""
    logger.info("Migrating response_templates table...")

    for cn, en in RISK_LEVEL_MAPPING.items():
        result = session.execute(
            text("UPDATE response_templates SET risk_level = :en WHERE risk_level = :cn"),
            {"en": en, "cn": cn}
        )
        logger.info(f"Updated {result.rowcount} rows: risk_level '{cn}' -> '{en}'")

    session.commit()
    logger.info("response_templates migration completed")

def migrate_data_security_entity_types(session):
    """Migrate data_security_entity_types table"""
    logger.info("Migrating data_security_entity_types table...")

    try:
        # This table uses 'category' field for risk levels
        for cn, en in DATA_RISK_LEVEL_MAPPING.items():
            result = session.execute(
                text("UPDATE data_security_entity_types SET category = :en WHERE category = :cn"),
                {"en": en, "cn": cn}
            )
            logger.info(f"Updated {result.rowcount} rows: category '{cn}' -> '{en}'")

        session.commit()
        logger.info("data_security_entity_types migration completed")
    except Exception as e:
        logger.warning(f"data_security_entity_types table migration skipped: {e}")
        session.rollback()

def migrate_ban_policies(session):
    """Migrate ban_policies table"""
    logger.info("Migrating ban_policies table...")

    try:
        for cn, en in RISK_LEVEL_MAPPING.items():
            result = session.execute(
                text("UPDATE ban_policies SET risk_level_threshold = :en WHERE risk_level_threshold = :cn"),
                {"en": en, "cn": cn}
            )
            logger.info(f"Updated {result.rowcount} rows: risk_level_threshold '{cn}' -> '{en}'")

        session.commit()
        logger.info("ban_policies migration completed")
    except Exception as e:
        logger.warning(f"ban_policies table may not exist: {e}")

def main():
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("Starting database migration: Chinese to English field values")
    logger.info("=" * 60)

    # Create database connection
    db_url = settings.database_url
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Run migrations
        migrate_detection_results(session)
        migrate_response_templates(session)
        migrate_data_security_entity_types(session)
        migrate_ban_policies(session)

        logger.info("=" * 60)
        logger.info("Migration completed successfully!")
        logger.info("All Chinese field values have been converted to English")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()

if __name__ == "__main__":
    main()
