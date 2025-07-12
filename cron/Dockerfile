# silhouet/cron/Dockerfile
FROM alpine:3.18

# Ensure package lists are updated and install cronie and postgresql-client
RUN apk update && apk add --no-cache cronie postgresql-client

# Create the /etc/crontabs directory if it doesn't exist and set correct permissions
# The cron daemon requires /etc/crontabs to be 0700 and files within it to be 0600
RUN mkdir -p /etc/crontabs && chmod 0700 /etc/crontabs

# Copy the crontab file and the cleanup script
COPY crontab /etc/crontabs/root
COPY cleanup_job.sh /usr/local/bin/cleanup_job.sh

# Set correct permissions for the crontab file (0600) and the script (+x)
RUN chmod 0600 /etc/crontabs/root && \
    chmod +x /usr/local/bin/cleanup_job.sh

# Ensure cronie daemon is running in foreground
# Removed all non-standard logging options to prevent unrecognized errors.
CMD ["crond", "-f"]
