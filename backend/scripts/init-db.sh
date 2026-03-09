#!/bin/bash
set -e

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        echo "Creating database: $db"
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
            SELECT 'CREATE DATABASE $db'
            WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
EOSQL
        echo "Enabling pgvector extension in: $db"
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$db" <<-EOSQL
            CREATE EXTENSION IF NOT EXISTS vector;
EOSQL
    done
    echo "Multiple databases created"
fi