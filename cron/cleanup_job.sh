#!/bin/sh
# silhouet/cron/cleanup_job.sh

# Ensure environment variables are loaded for psql connection
# These vars are defined in .env and passed via docker-compose env_file
export PGPASSWORD="${POSTGRES_PASSWORD}"
export PGUSER="${POSTGRES_USER}"
export PGDATABASE="${POSTGRES_DB}"
export PGHOST="db" # 'db' is the service name of the postgres container

echo "Running daily post cleanup job at $(date)"

# Execute the DELETE command using psql
# -c: runs the command string
# -q: quiet mode (no messages from psql itself)
# -At: suppress header, footer, and align columns, useful for scripting output
psql -h "${PGHOST}" -U "${PGUSER}" -d "${PGDATABASE}" -c "DELETE FROM posts WHERE created_at < NOW() - INTERVAL '1 month';"

# Check the exit status of the psql command
if [ $? -eq 0 ]; then
    echo "Post cleanup job completed successfully."
else
    echo "ERROR: Post cleanup job failed."
fi

echo "Cleanup job finished at $(date)"
