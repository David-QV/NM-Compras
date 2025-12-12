# Imagen base
FROM python:3.11-slim

# Configuración base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Variables específicas (conexión ya embebida)
ENV DATABASE_URL="mysql+pymysql://newmerid_compras_user:9yBKaU,yy_SABleg@65.99.225.174:3306/newmerid_compras"
ENV APP_NAME="Compras API"
ENV DEBUG=false

# Instalar dependencias del sistema y MySQL client
RUN apt-get update && apt-get install -y \
    build-essential \
    default-mysql-client \
    libmariadb-dev-compat \
    libmariadb-dev && \
    rm -rf /var/lib/apt/lists/*

# Crear carpeta de trabajo
WORKDIR /app

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Exponer el puerto FastAPI
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
