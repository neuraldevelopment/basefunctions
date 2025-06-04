# Docker Compose configuration for SQLite database instance: {{ instance_name }}
version: '3.8'

services:
  sqlite-web:
    image: coleifer/sqlite-web
    container_name: {{ instance_name }}_sqlite_web
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    command: ["--host", "0.0.0.0", "--port", "8080", "/data/{{ instance_name }}.db"]
    volumes:
      - {{ data_dir }}:/data
    ports:
      - "{{ admin_port }}:8080"
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8080/"]
      interval: 15m
      timeout: 30s
      retries: 3
      start_period: 30s

networks:
  default:
    name: {{ instance_name }}_network