# Flask App con Docker

Este proyecto contiene una aplicación Flask lista para ser ejecutada en un contenedor Docker. A continuación, se describen los pasos necesarios para desplegar y ejecutar la aplicación.

---

## Requisitos Previos

Asegurarse de tener instalados los siguientes programas en el servidor:

- [Docker](https://www.docker.com/)

---

## Variables de Entorno

La aplicación requiere las siguientes variables de entorno para la autenticación con la API de **RED5G**:

- `USERNAME`: nombre de usuario para la API.
- `PASSWORD`: contraseña para la API.

Se puede configurar directamente en el **Dockerfile** o pasarlas al contenedor durante la ejecución.

---

## Pasos para el Despliegue

### 1. Construir la Imagen Docker

Ejecuta el siguiente comando para construir la imagen de Docker desde el archivo `Dockerfile`:

```bash
docker build -t app-pdf .
```

### 2. Ejecutar el Contenedor

Para ejecutar el contenedor y exponer la aplicación en el puerto 5000, usar el siguiente comando:

```bash
docker run -p 5000:5000 app-pdf
```


---

## Despliegue con Variables de Entorno desde un Archivo `.env`

Puedes gestionar las variables de entorno utilizando un archivo `.env`. Crea un archivo `.env` en el directorio raíz del proyecto con el siguiente contenido:

```env
USERNAME=<tu_usuario>
PASSWORD=<tu_contraseña>
```

Luego, ejecuta el contenedor con:

```bash
docker run --env-file .env -p 5000:5000 app-pdf
```

---

## Estructura del Proyecto

La estructura del proyecto es la siguiente:

```
/app
├── app.py               # Archivo principal de la aplicación Flask
├── requirements.txt     # Dependencias de Python
├── Dockerfile           # Archivo de configuración de Docker
└── .env                 # Archivo opcional para variables de entorno
```

---

## Verificar la Aplicación

Una vez que el contenedor esté en ejecución, la aplicación estará disponible en:

```
http://localhost:5000
```

---

## Detener el Contenedor

Para detener el contenedor en ejecución, encuentra su **CONTAINER ID** con:

```bash
docker ps
```

Y luego detén el contenedor con:

```bash
docker stop <CONTAINER_ID>
```

---
