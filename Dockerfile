 
# Dockerfile
FROM python:3.9

ARG PIP_TRUSTED_HOSTS_STR="pypi.org files.pythonhosted.org pypi.python.org"

WORKDIR /app

COPY requirements.txt .

RUN echo "Configuring pip with trusted hosts: \"${PIP_TRUSTED_HOSTS_STR}\"" && \
    pip config set global.trusted-host "${PIP_TRUSTED_HOSTS_STR}" && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3011

CMD ["python", "app.py"]
