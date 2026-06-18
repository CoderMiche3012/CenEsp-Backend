
---

```markdown
# Backend CEI - Sistema Integral con Machine Learning 🛡️🤖

Este proyecto contiene el backend del Sistema Integral para el Centro de Esperanza Infantil A.C. (CEI). Implementa una arquitectura robusta que incluye una base de datos relacional normalizada, validaciones de seguridad mediante expresiones regulares, autenticación segura con JSON Web Tokens (JWT), un módulo desacoplado de Inteligencia Artificial para la priorización de beneficiarios y un sistema automatizado de carga masiva de datos geográficos.

## 🛠️ Tecnologías Utilizadas
* Python 3.13.7
* Django 6.0.1 & Django REST Framework (DRF)
* Scikit-Learn 1.5.0 & Joblib 1.4.2 (Módulo de IA)
* PostgreSQL (Base de datos)
* Docker & Docker Compose (Contenerización del entorno)
* SimpleJWT (Autenticación)

---

## 🚀 Guía de Instalación y Configuración con Docker

Sigue estos pasos para levantar todo el entorno de desarrollo (Backend, Frontend y Base de Datos) de forma local utilizando contenedores.

### 1. Levantar los Contenedores
Asegúrate de tener Docker Desktop ejecutándose. En la raíz del proyecto (donde se encuentra el archivo `docker-compose.yml`), ejecuta el siguiente comando para construir las imágenes y encender los servicios en segundo plano:
```bash
docker compose up --build -d

```

### 2. Base de Datos y Migraciones

Una vez que los contenedores estén activos, ejecuta las migraciones para crear la estructura de tablas correspondiente en PostgreSQL dentro del contenedor del backend:

```bash
# Preparar los archivos de migración si existen cambios en los modelos
docker compose exec backend python manage.py makemigrations

# Aplicar las migraciones en la base de datos contenerizada
docker compose exec backend python manage.py migrate

```

### 3. Poblar la Base de Datos (Data Seeding)

Ejecuta los comandos personalizados para inyectar la información inicial requerida por el sistema:

```bash
# Cargar la matriz estática de roles y permisos (Administrador, Trabajadora Social, etc.)
docker compose exec backend python manage.py setup_roles

# Inyección masiva de más de 7,000 códigos postales y colonias de Oaxaca (Valida duplicados)
docker compose exec backend python manage.py cargar_sepomex

```

### 4. Crear el Superusuario (Administrador)

Para acceder al panel de administración integrado de Django, interactúa con el contenedor para generar las credenciales maestras:

```bash
docker compose exec backend python manage.py createsuperuser

```

**Credenciales de acceso sugeridas para el entorno de pruebas:**

* **Usuario:** `admin`
* **Correo:** `admin2026@gmail.com`
* **Password:** `admin123456-`

### 5. Verificación del Entorno

* El servidor de la API REST estará disponible en: `http://127.0.0.1:8000/`
* El panel de administración de Django se encuentra en: `http://127.0.0.1:8000/admin/`

---

## 🔌 Directorio de la API (Endpoints)

Todas las rutas base para el frontend comienzan con: `http://127.0.0.1:8000/`

### Autenticación (JWT)

| Método | Ruta | Descripción | Requiere Token |
| --- | --- | --- | --- |
| **POST** | `/api/cuentas/login/` | Recibe `nom_usuario` y `password`. Devuelve los tokens `access` y `refresh`. | ❌ No |
| **POST** | `/api/cuentas/login/refresh/` | Recibe el token de `refresh` y devuelve un nuevo token de `access`. | ❌ No |

### Gestión de Usuarios

| Método | Ruta | Descripción | Requiere Token |
| --- | --- | --- | --- |
| **POST** | `/api/cuentas/registro/` | Crea un nuevo usuario aplicando las validaciones del sistema. | ❌ No |
| **GET** | `/api/cuentas/usuarios/` | Lista todos los usuarios registrados en la plataforma. | ✅ Sí |
| **GET** | `/api/cuentas/usuarios/{id}/` | Detalles específicos de un usuario por su ID. | ✅ Sí |
| **PUT/PATCH** | `/api/cuentas/usuarios/{id}/` | Actualiza la información de un usuario específico. | ✅ Sí |
| **DELETE** | `/api/cuentas/usuarios/{id}/` | Realiza la eliminación de un usuario. | ✅ Sí |

### 📚 Configuración Escolar (Sprint 2)

| Método | Ruta | Descripción | Requiere Token |
| --- | --- | --- | --- |
| **GET** | `/api/periodos/periodos/` | Lista todos los periodos y ciclos escolares activos. | ✅ Sí |
| **POST** | `/api/periodos/periodos/` | Crea un nuevo periodo (Valida de forma estricta el formato YYYY-YYYY). | ✅ Sí |
| **PUT/DELETE** | `/api/periodos/periodos/{id}/` | Modifica o elimina un periodo escolar específico. | ✅ Sí |

### 🧾 1. Flujo de Postulación (App Beneficiarios)

| Método | Ruta | Descripción | Requiere Token |
| --- | --- | --- | --- |
| **GET/POST** | `/api/beneficiarios/direcciones/` | Gestiona las direcciones físicas de los postulantes. | ✅ Sí |
| **GET/POST** | `/api/beneficiarios/expedientes/` | Gestiona los expedientes base (Datos personales vinculados a la dirección). | ✅ Sí |
| **POST** | `/api/beneficiarios/postulantes/` | **Ruta Maestra:** Registra Dirección, Expediente y Postulante procesando un JSON anidado. | ✅ Sí |
| **GET/POST** | `/api/beneficiarios/visitas/` | Agenda, controla y gestiona el historial de visitas domiciliarias. | ✅ Sí |

### 📊 2. Estudio Socioeconómico e Inteligencia Artificial (App Estudios / modeloML)

| Método | Ruta | Descripción | Requiere Token |
| --- | --- | --- | --- |
| **GET** | `/api/estudios/estudios/` | Obtiene el listado completo de los estudios socioeconómicos evaluados. | ✅ Sí |
| **POST** | `/api/estudios/estudios/` | **Ruta Predictiva:** Guarda el estudio (familia, vivienda, ingresos). Dispara de forma interna la señal de Django (`signals.py`) ejecutando en milisegundos el Clasificador de Árbol de Decisión (.joblib) bajo los umbrales de CONEVAL para asignar la prioridad (Alta, Media, Baja). | ✅ Sí |
| **GET/PUT** | `/api/estudios/estudios/{id}/` | Consulta o actualiza un estudio socioeconómico específico y reevalúa el modelo predictivo de ser necesario. | ✅ Sí |

### ✅ 3. Aceptación, Consulta Integral y Evidencias

| Método | Ruta | Descripción | Requiere Token |
| --- | --- | --- | --- |
| **GET/POST** | `/api/beneficiarios/beneficiarios/` | Formaliza el estatus de un candidato a Beneficiario Oficial ligándolo a su expediente. | ✅ Sí |
| **GET** | `/api/beneficiarios/beneficiarios/{id}/` | **Endpoint de Consulta Integral:** Retorna los datos detallados de un beneficiario, acoplando en una sola respuesta sus antecedentes de visitas, los resultados de su estudio socioeconómico y el nivel de prioridad calculado por la IA. | ✅ Sí |
| **PUT/DELETE** | `/api/beneficiarios/beneficiarios/{id}/` | Actualiza de manera directa el estatus operativo, bitácoras o notas del beneficiario activo. | ✅ Sí |
| **POST/GET** | `/api/beneficiarios/fotografias/` | Módulo de carga de archivos multimedia para almacenar la evidencia fotográfica del proceso completo del beneficiario. | ✅ Sí |

### 🌍 Catálogos Geográficos (SEPOMEX y Entidades)

| Método | Ruta | Descripción | Requiere Token |
| --- | --- | --- | --- |
| **GET** | `/api/ubicacion/codigos-postales/` | Consulta dinámica y filtrada de los asentamientos y códigos postales precargados de Oaxaca. | ✅ Sí |
| **GET** | `/api/ubicacion/municipios/` | Devuelve el catálogo completo de los municipios del estado de Oaxaca para optimización de formularios en el frontend. | ✅ Sí |

### Roles y Permisos (Estructura del Sistema)

| Método | Ruta | Descripción | Requiere Token |
| --- | --- | --- | --- |
| **GET** | `/api/cuentas/roles/` | Devuelve la lista estática de Roles de usuario del sistema (útil para selectores en React). | ❌ No |
| **GET** | `/api/cuentas/permisos/` | Devuelve la matriz técnica completa de permisos mapeados en el backend. | ❌ No |

> **Nota de Integración para el Frontend (React):** Toda petición marcada con un token obligatorio (✅) debe incorporar en las cabeceras HTTP el esquema de autorización correspondiente:
> ```http
> Authorization: Bearer <token_access_generado>
> 
> ```
> 
> 

```

***

Este archivo ya queda completamente listo para el repositorio y describe con la precisión que el equipo de TI y el sínodo necesitan. ¿Te parece bien que pasemos a redactar las descripciones detalladas de las Historias de Usuario faltantes que detectamos en el reporte del Sprint 6?

```