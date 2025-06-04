# Docker Compose configuration for MySQL database instance: {{ instance_name }}
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: {{ instance_name }}_mysql
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    environment:
      MYSQL_ROOT_PASSWORD: "{{ db_password }}"
      MYSQL_DATABASE: {{ instance_name }}
      MYSQL_USER: {{ instance_name }}_user
      MYSQL_PASSWORD: "{{ db_password }}" 
    volumes:
      - {{ data_dir }}/mysql:/var/lib/mysql
      - ./bootstrap:/docker-entrypoint-initdb.d
    ports:
      - "{{ db_port }}:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 15m
      timeout: 30s
      retries: 3
      start_period: 30s

  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    container_name: {{ instance_name }}_phpmyadmin
    {% if auto_restart %}restart: unless-stopped{% else %}restart: "no"{% endif %}
    environment:
      PMA_HOST: mysql
      PMA_USER: root
      PMA_PASSWORD: test
      PMA_ARBITRARY: 1
    volumes:
      - {{ data_dir }}/phpmyadmin:/sessions
    ports:
      - "{{ admin_port }}:80"
    depends_on:
      mysql:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 15m
      timeout: 30s
      retries: 3
      start_period: 60s

networks:
  default:
    name: {{ instance_name }}_network