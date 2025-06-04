# Docker Compose configuration for PostgreSQL database instance: {{ instance_name }}
version: '3.8'

services:
  postgres:
    image: postgres:14
    container_name: {{ instance_name }}_postgres
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    environment:
      POSTGRES_PASSWORD: "{{ db_password }}"  # From template variable
      POSTGRES_USER: postgres
      POSTGRES_DB: postgres
    volumes:
      - {{ data_dir }}/postgres:/var/lib/postgresql/data
      - ./bootstrap:/docker-entrypoint-initdb.d  # Script will run on first start
    ports:
      - "{{ db_port }}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 15m
      timeout: 30s
      retries: 3
      start_period: 30s

  pgadmin:
    image: dpage/pgadmin4
    container_name: {{ instance_name }}_pgadmin
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: "{{ db_password }}"  # From template variable
      PGADMIN_CONFIG_SERVER_MODE: 'False'
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: 'False'  # Keine Master-Passwort-Abfrage
      PGADMIN_CONFIG_WTF_CSRF_ENABLED: 'False'  # Deaktiviert CSRF Protection
    volumes:
      - {{ data_dir }}/pgadmin:/var/lib/pgadmin
      - ./config/pgadmin_servers.json:/pgadmin4/servers.json  # Korrekt: pgAdmin
    ports:
      - "{{ admin_port }}:80"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/misc/ping"]
      interval: 15m
      timeout: 30s
      retries: 3
      start_period: 60s

networks:
  default:
    name: {{ instance_name }}_network