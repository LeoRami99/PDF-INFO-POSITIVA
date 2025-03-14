# Imagen base de Python
FROM python:3.9-slim


# ENV VARIABLES PARA LA AUTENTICACIÓN DE LA API DE RED5G

ENV APP_PDF_USERNAME=
ENV APP_PDF_PASSWORD=

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo de requerimientos
COPY requirements.txt .

# Instalar las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos de la aplicación al contenedor
COPY . .

# Establecer la variable de entorno para habilitar el modo de desarrollo de Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Exponer el puerto en el que Flask corre
EXPOSE 5000

# Comando para iniciar la aplicación
CMD ["flask", "run"]
