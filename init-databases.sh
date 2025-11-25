#!/bin/bash
set -e

create_database() {
    local db_name=$1
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
        CREATE DATABASE $db_name;
        GRANT ALL PRIVILEGES ON DATABASE $db_name TO $POSTGRES_USER;
EOSQL
}

echo "Creating databases from: $POSTGRES_MULTIPLE_DATABASES"

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        echo "Creating database: $db"
        
        existing=$(psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" --dbname "postgres" -tAc "SELECT 1 FROM pg_database WHERE datname='$db'")
        
        if [ -z "$existing" ]; then
            create_database "$db"
            echo "Database $db created"
        else
            echo "Database $db already exists, skipping"
        fi
    done
    echo "Databases created successfully"
fi