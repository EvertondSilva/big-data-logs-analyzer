#!/bin/bash
# wait-for-postgres.sh

set -e

host="$1"
shift
cmd="$@"

until PGPASSWORD=$DB_PASSWORD psql -h "$host" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  >&2 echo "⏳ PostgreSQL não está pronto - aguardando..."
  sleep 2
done

>&2 echo "✅ PostgreSQL está pronto - executando comando"
exec $cmd