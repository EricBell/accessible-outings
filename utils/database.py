"""Database compatibility utilities for SQLite and PostgreSQL."""

import json
from sqlalchemy import Text, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from flask import current_app


class DatabaseCompatArray(TypeDecorator):
    """A type that can store arrays in both PostgreSQL and SQLite."""
    
    impl = Text
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(Text))
        else:
            return dialect.type_descriptor(Text)
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            # For SQLite, store as JSON string
            return json.dumps(value) if value else None
    
    def process_result_value(self, value, dialect):
        if value is None:
            return []
        if dialect.name == 'postgresql':
            return value or []
        else:
            # For SQLite, parse JSON string
            try:
                return json.loads(value) if value else []
            except (json.JSONDecodeError, TypeError):
                return []


class DatabaseCompatJSON(TypeDecorator):
    """A type that can store JSON in both PostgreSQL and SQLite."""
    
    impl = Text
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB)
        else:
            return dialect.type_descriptor(Text)
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            # For SQLite, store as JSON string
            return json.dumps(value) if value else None
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        else:
            # For SQLite, parse JSON string
            try:
                return json.loads(value) if value else None
            except (json.JSONDecodeError, TypeError):
                return None


def get_database_type():
    """Get the current database type from configuration."""
    try:
        return current_app.config.get('DATABASE_TYPE', 'sqlite')
    except RuntimeError:
        # Outside application context
        import os
        database_url = os.environ.get('DATABASE_URL', 'sqlite:///accessible_outings.db')
        return 'sqlite' if database_url.startswith('sqlite') else 'postgresql'


def is_sqlite():
    """Check if we're using SQLite."""
    return get_database_type() == 'sqlite'


def is_postgresql():
    """Check if we're using PostgreSQL."""
    return get_database_type() == 'postgresql'


def create_database_agnostic_query(base_query, sqlite_query, postgresql_query):
    """Execute different queries based on database type."""
    if is_postgresql():
        return postgresql_query
    else:
        return sqlite_query
