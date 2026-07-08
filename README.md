# FactorIA 🏭

FactorIA es una aplicación en Python diseñada bajo los principios de **Arquitectura Limpia (Clean Architecture)** y **Diseño Guiado por el Dominio (DDD)**. Simula la monitorización y control de una planta industrial de máquinas que incorporan autómatas programables (PLC) y diferentes tipos de sensores.

El proyecto está completamente dockerizado, utiliza **PostgreSQL** para la persistencia de datos, **SQLAlchemy** como ORM, y **Alembic** para el control de versiones del esquema de base de datos (migraciones).

---

## 🏗️ Arquitectura del Proyecto

El sistema está separado en capas para desacoplar las reglas de negocio de la tecnología de persistencia:

```
factorIA/
├── alembic/                  # Configuraciones y versiones de migración de la Base de Datos
├── src/
│   ├── Exceptions/           # Excepciones personalizadas de dominio e infraestructura
│   ├── domain/               # Capa de Dominio (Reglas de negocio puras)
│   │   ├── machine.py
│   │   ├── plc.py
│   │   └── sensor.py         # Incluye SensorFactory
│   ├── storage/              # Capa de Persistencia (Detalles de infraestructura)
│   │   ├── connectors/       # Conexiones externas (PostgreSQL engine/session)
│   │   ├── entities/         # Modelos ORM de SQLAlchemy (MachineORM, PLCORM, SensorORM)
│   │   ├── repositories/     # Patrón Repository (Traductores Dominio <-> ORM)
│   │   └── seed/             # Script de semillas para poblar la BD
│   └── app.py                # Orquestador del flujo de la aplicación
├── Dockerfile                # Empaquetado optimizado con 'uv'
├── docker-compose.yml        # Orquestación de contenedores y variables de entorno
└── main.py                   # Punto de arranque de la aplicación
```

### 🧠 Conceptos Clave de la Arquitectura
*   **Capa de Dominio**: Modela la realidad del negocio de manera aislada (`Machine`, `PLC`, `Sensor`, `SensorFactory`). No sabe de la existencia de bases de datos, SQLAlchemy o redes.
*   **Capa de Persistencia**: Mapea las tablas (`entities/*_orm.py`) y define repositorios (`MachineRepository`) encargados de guardar y recuperar los objetos transformándolos a dominio puro.
*   **Inyección de Dependencias**: La base de datos es inicializada en `main.py` y se le inyecta la sesión a `App` al arrancar.

---

## 🗄️ Esquema de Base de Datos

El diseño de la base de datos relacional en PostgreSQL sigue el siguiente esquema de tablas y relaciones de uno a uno (1:1) y uno a muchos (1:N):

```mermaid
erDiagram
    machines {
        integer id PK
        string name UK
    }
    plcs {
        integer id PK
        integer owner_id FK
    }
    sensors {
        integer id PK
        string name
        integer owner_id FK
        float failure_probability
        varchar_array error_codes
    }

    machines ||--|| plcs : "Tiene un (1:1)"
    plcs ||--o{ sensors : "Contiene varios (1:N)"
```

*   **machines**: Guarda las máquinas de la planta industrial. Su nombre es único e indexado.
*   **plcs**: Registra los autómatas programables de control. Tiene una relación **1 a 1** con `machines` mediante `owner_id`.
*   **sensors**: Almacena los diferentes sensores. Tiene una relación **1 a Muchos** con `plcs` mediante `owner_id`. Guarda la probabilidad de fallo y la lista nativa de Postgres (`ARRAY`) para los códigos de error asociados.

---

## 🐋 Infraestructura con Docker y Docker Compose

La aplicación se compone de dos contenedores que se comunican de forma aislada a través de una red interna de Docker:

1.  **`db` (factoria_db)**: Contenedor PostgreSQL 16 con volumen persistente para no perder los datos al detener el entorno.
2.  **`app` (factoria_app)**: Aplicación Python construida dinámicamente con la herramienta de paquetes rápida `uv`.

### 🔒 Seguridad y Configuración (.env)
Las credenciales de base de datos no se guardan en el código. Se leen desde el archivo local `.env` (excluido en git):

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_contrasena_segura
POSTGRES_DB=factoria
```

---

## 🚀 Guía de Uso Rápido

Sigue estos comandos desde la raíz del proyecto para gestionar el ciclo de vida del entorno:

### 1. Levantar todo el ecosistema (Migraciones + Seeds + App)
El contenedor de la aplicación esperará de forma automática a que la base de datos esté lista. Luego ejecutará las migraciones pendientes de Alembic, insertará las máquinas iniciales (si no existen) y arrancará la monitorización:

```bash
docker-compose up --build
```

### 2. Ver logs en tiempo real
Puedes monitorizar la salida de los contenedores en cualquier momento:

```bash
# Ver todos los logs
docker-compose logs -f

# Ver solo los logs de la aplicación de monitorización
docker-compose logs -f app
```

### 3. Detener el proyecto
Detener y apagar los contenedores de forma segura (los datos de la BD **se mantienen** intactos):

```bash
docker-compose down
```

### 4. Limpieza total (Borrar Base de Datos)
Si quieres borrar todos los datos de la base de datos para simular un arranque limpio con semillas desde cero:

```bash
docker-compose down -v
```

---

## 🛠️ Desarrollo Local y Alembic (Migraciones)

Si realizas modificaciones en las entidades de `src/storage/entities/` y necesitas generar nuevas migraciones desde tu máquina local hacia el contenedor de base de datos:

### Generar una nueva migración (Autogenerada)
Asegúrate de tener el contenedor de la base de datos levantado (`docker-compose up -d db`), carga las variables de entorno de tu `.env` y ejecuta:

```bash
export $(grep -v '^#' .env | xargs) && DATABASE_URL=postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB uv run alembic revision --autogenerate -m "Descripción de los cambios"
```

### Aplicar migraciones localmente
```bash
export $(grep -v '^#' .env | xargs) && DATABASE_URL=postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB uv run alembic upgrade head
```

---

## 🌱 Semillas (Seeds)
Al arrancar el contenedor, el script de semillas en `src/storage/seed/seed.py` se autoejecuta. Este comprueba mediante una consulta si existen máquinas en base de datos. Si el resultado es cero, insertará por defecto la configuración inicial de máquinas de la planta (`Turbine-A`, `Compressor-B`, `Robotic-Harm-C` y `Transport-D`) con sus respectivos sensores y probabilidades de fallo.
