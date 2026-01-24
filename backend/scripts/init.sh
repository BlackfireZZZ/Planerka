
set -e

echo "Starting initialization..."
if [ -f /app/scripts/migrate.sh ]; then
    sh /app/scripts/migrate.sh
else
    echo "Warning: migrate.sh not found, skipping migrations"
fi
echo "Starting application..."
exec "$@"

