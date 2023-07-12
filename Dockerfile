 
# Dockerfile
FROM python:3.9.17-slim

ARG PIP_TRUSTED_HOSTS_STR="pypi.org files.pythonhosted.org pypi.python.org"

WORKDIR /app

COPY requirements.txt .

RUN echo "Installing curl" && apt-get clean all && \
    apt-get update; \
    apt-get install curl && \ 
    echo "Configuring pip with trusted hosts: \"${PIP_TRUSTED_HOSTS_STR}\"" && \
    pip config set global.trusted-host "${PIP_TRUSTED_HOSTS_STR}" && \
    pip install --no-cache-dir -r requirements.txt && \
    echo "Cleaning.." && \
    apt-get clean && \ 
    rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 3011

CMD ["python", "app.py"]
