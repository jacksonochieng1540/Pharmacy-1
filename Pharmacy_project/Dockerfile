
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


WORKDIR /app


RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


COPY . /app/


RUN mkdir -p /app/media /app/staticfiles


RUN python manage.py collectstatic --noinput || true


RUN echo '#!/bin/bash\n\
echo "Waiting for postgres..."\n\
while ! nc -z db 5432; do\n\
  sleep 0.1\n\
done\n\
echo "PostgreSQL started"\n\
\n\
echo "Running migrations..."\n\
python manage.py migrate --noinput\n\
\n\
echo "Creating superuser..."\n\
python manage.py shell <<EOF\n\
from django.contrib.auth import get_user_model\n\
User = get_user_model()\n\
if not User.objects.filter(username="admin").exists():\n\
    User.objects.create_superuser("admin", "admin@pharmacy.com", "admin123", role="admin")\n\
    print("Superuser created")\n\
else:\n\
    print("Superuser already exists")\n\
EOF\n\
\n\
echo "Starting server..."\n\
exec "$@"' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh


EXPOSE 8000


ENTRYPOINT ["/app/entrypoint.sh"]


CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
