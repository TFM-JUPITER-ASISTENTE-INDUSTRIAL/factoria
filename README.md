# FactorIA 🏭

FactorIA es una plataforma industrial en Python diseñada bajo los principios de **Arquitectura Limpia (Clean Architecture)** y **Diseño Guiado por el Dominio (DDD)**. Simula la monitorización y control en tiempo real de una planta industrial de máquinas con autómatas programables (PLC), sensores de diferentes tipos y probabilidades de fallo, y un servidor **API REST (FastAPI)** para consulta y gestión de alarmas.

El proyecto está completamente dockerizado, utiliza **PostgreSQL** para la persistencia de datos, **SQLAlchemy 2.0** como ORM, **Alembic** para el control de versiones del esquema de base de datos y **uv** para la gestión ultrarrápida de paquetes.

---

## 🏗️ Arquitectura del Proyecto

El sistema desacopla estrictamente las reglas de negocio de la tecnología de persistencia y de la capa de entrega (HTTP / API):

```text
factorIA/
├── alembic/                      # Configuraciones y versiones de migración de la Base de Datos
├── src/
│   ├── api/                      # Capa de Entrada / Entrega HTTP (FastAPI)
│   │   ├── dependencies.py       # Inyección de dependencias (Sesión de BD con yield)
│   │   ├── main.py               # Instancia de FastAPI, middlewares (CORS) y registro de routers
│   │   ├── routes/               # Controladores / Endpoints REST
│   │   │   ├── alarms.py         # Endpoints para /alarms y resolución de incidencias
│   │   │   ├── machines.py       # Endpoints para /machines y detalle de sensores
│   │   │   └── status.py         # Endpoint para /status (resumen ejecutivo de planta)
│   │   └── schemas/              # DTOs / Modelos Pydantic v2 (Validación y serialización)
│   │       ├── alarm_schema.py
│   │       ├── machine_schema.py
│   │       └── status_schema.py
│   ├── config/                   # Configuración global (Logger, etc.)
│   │   └── logger.py
│   ├── domain/                   # Capa de Dominio (Reglas de negocio puras e independientes)
│   │   ├── alarm.py              # Entidad Alarm y enumeración AlarmStatus (ACTIVE, SOLVED)
│   │   ├── machine.py            # Entidad Machine y MachineStatus (ONLINE, ERROR, MAINTENANCE)
│   │   ├── plc.py                # Entidad PLC (colector de sensores)
│   │   └── sensor.py             # Sensor base, implementaciones especializadas y SensorFactory
│   ├── Exceptions/               # Excepciones personalizadas de dominio e infraestructura
│   │   ├── database_exception.py
│   │   └── plc_exception.py
│   ├── storage/                  # Capa de Persistencia (Infraestructura de datos)
│   │   ├── connectors/           # Conexión SQLAlchemy a PostgreSQL (Engine / SessionLocal)
│   │   │   └── postgresql.py
│   │   ├── entities/             # Modelos ORM de SQLAlchemy
│   │   │   ├── alarm_orm.py
│   │   │   ├── machine_orm.py
│   │   │   ├── plc_orm.py
│   │   │   └── sensor_orm.py
│   │   ├── repositories/         # Patrón Repository (Mapeo BD <-> Dominio enriquecido)
│   │   │   ├── alarm_repository.py
│   │   │   └── machine_repository.py
│   │   └── seed/                 # Script de semillas para poblar la BD inicial
│   │       └── seed.py
│   └── app.py                    # Orquestador del bucle de simulación en segundo plano
├── tests/                        # Suite de pruebas automatizadas con pytest
│   └── test_machine.py
├── Dockerfile                    # Empaquetado optimizado con 'uv'
├── docker-compose.yml            # Orquestación de 3 servicios (db, simulator, api)
├── main.py                       # Punto de entrada del proceso de simulación
└── pyproject.toml                # Gestión de dependencias del proyecto
```

---

## 🗄️ Esquema de Base de Datos

El diseño de base de datos relacional en PostgreSQL sigue el siguiente esquema entidad-relación:

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
    alarms {
        integer id PK
        integer sensor_id FK
        integer machine_id FK
        string error_code
        string status
        timestamp triggered_at
        timestamp resolved_at
    }

    machines ||--|| plcs : "Tiene un (1:1)"
    plcs ||--o{ sensors : "Contiene varios (1:N)"
    machines ||--o{ alarms : "Registra (1:N)"
    sensors ||--o{ alarms : "Dispara (1:N)"
```

### 📋 Descripción de Tablas
* **`machines`**: Guarda las máquinas de la planta con nombre único indexado.
* **`plcs`**: Registra los autómatas de control (relación 1:1 con `machines`).
* **`sensors`**: Sensores asociados al PLC (relación 1:N). Guarda probabilidad de fallo y lista de códigos de error (`ARRAY`).
* **`alarms`**: Registra las alarmas generadas en la planta con fecha de disparo y resolución. Posee un **índice parcial único** (`sensor_id`, `error_code` WHERE `status = 'ACTIVE'`) que previene duplicados mientras una alarma siga activa.

---

## 🌐 API REST (FastAPI)

La aplicación incluye un servidor API REST de alto rendimiento con documentación OpenAPI interactiva:

* **Swagger UI (Interactivo)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc (Documentación)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 📌 Tabla de Endpoints

| Método | Endpoint | Descripción | Parámetros / Filtros |
| :---: | :--- | :--- | :--- |
| `GET` | `/status` | Resumen global del estado de la planta y contador de alarmas | Ninguno |
| `GET` | `/machines` | Lista todas las máquinas con su estado (`ONLINE`/`ERROR`) y sensores | Ninguno |
| `GET` | `/machines/{machine_id}` | Obtiene el detalle de una máquina específica por su ID | `machine_id: int` |
| `GET` | `/alarms` | Lista las alarmas de la factoría | `status: Optional[AlarmStatus]`, `machine_id: Optional[int]` |
| `GET` | `/alarms/{alarm_id}` | Detalle de una alarma específica por su ID | `alarm_id: int` |
| `PATCH` | `/alarms/{alarm_id}/resolve` | Resuelve una alarma activa (`SOLVED`) asignando la marca temporal actual | `alarm_id: int` |

---

## 🐋 Infraestructura con Docker Compose

La solución se compone de 3 servicios aislados comunicados mediante la red interna `factoria-network`:

1. **`db` (`factoria_db`)**: Contenedor PostgreSQL 16 Alpine con comprobación de salud (`healthcheck`) y volumen persistente (`postgres_data`).
2. **`simulator` (`factoria_app`)**: Proceso en segundo plano que ejecuta el ciclo de simulación y monitorización continua cada segundo (`main.py`).
3. **`api` (`factoria_api`)**: Servidor ASGI FastAPI servido con `uvicorn` en el puerto `8000:8000`.

### 🔒 Variables de Entorno (`.env`)
Las credenciales se gestionan desde un archivo local `.env` (excluido en git):

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_contrasena_segura
POSTGRES_DB=factoria
```

---

## 🚀 Guía de Uso Rápido

Ejecuta estos comandos desde la raíz del proyecto para gestionar el ciclo de vida del ecosistema:

### 1. Crear la configuración local

El archivo `.env` no se descarga desde GitHub porque contiene la configuración local de cada equipo. Créalo a partir de la plantilla versionada:

```bash
cp .env.example .env
```

Revisa sus valores antes de continuar y no subas `.env` al repositorio.

### 2. Levantar todo el ecosistema (Migraciones + Seed + Simulador + API)

Los contenedores esperarán a que PostgreSQL esté listo. El servicio `simulator` aplicará las migraciones de Alembic, sincronizará el catálogo de máquinas y alarmas mediante el seed y, por último, iniciará la simulación:

```bash
docker compose up --build -d
```

> Ejecutar únicamente `docker compose up -d db` levanta PostgreSQL, pero no aplica las migraciones ni importa el catálogo. Para realizar la inicialización automática también debe arrancarse `simulator`.

### 3. Ver logs en tiempo real
```bash
# Ver todos los logs combinados
docker compose logs -f

# Ver únicamente los logs de la API REST
docker compose logs -f api

# Ver únicamente los logs del simulador de planta
docker compose logs -f simulator
```

### 4. Detener el proyecto de forma segura
Mantiene intactos los datos almacenados en PostgreSQL:

```bash
docker compose down
```

### 5. Reinicio limpio desde cero (Borrar Base de Datos)
Para destruir los volúmenes, tablas y registros y reiniciar la simulación con datos vírgenes:

```bash
docker compose down -v
```

> **Atención:** `down -v` elimina todo el contenido de PostgreSQL. No debe utilizarse si se quieren conservar los datos.

---

## 🛠️ Desarrollo Local y Tests

### Ejecutar Tests Automatizados con Pytest
```bash
uv run pytest -o pythonpath=.
```

### Ejecutar la API en Local (fuera de Docker)
Asegúrate de tener la base de datos levantada (`docker-compose up -d db`) y ejecuta:
```bash
uv run uvicorn src.api.main:app --reload --port 8000
```

### Generar y Aplicar Migraciones de Base de Datos (Alembic)
```bash
# Generar una nueva migración autogenerada por cambios en entities/
export $(grep -v '^#' .env | xargs) && DATABASE_URL=postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB uv run alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones pendientes
export $(grep -v '^#' .env | xargs) && DATABASE_URL=postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB uv run alembic upgrade head
```

---

## 🌱 Semillas Iniciales (Seeds)

Al clonar el repositorio, PostgreSQL todavía no contiene datos. El proyecto incluye las migraciones, cinco catálogos CSV en `data/alarm_catalogs/` y un seed que importa automáticamente:

| Máquina | Identificador externo | Definiciones de alarma |
| :--- | :--- | ---: |
| Denester | `DENESTER-01` | 30 |
| Encajadora | `ENCAJADORA-01` | 30 |
| Estuchadora | `ESTUCHADORA-01` | 35 |
| Serializadora | `SERIALIZADORA-01` | 35 |
| Termoformadora | `TERMOFORMADORA-01` | 35 |
| **Total** | **5 máquinas** | **165** |

El servicio `simulator` ejecuta automáticamente esta secuencia al arrancar:

```text
alembic upgrade head
        ↓
python -m src.storage.seed.seed
        ↓
main.py
```

El seed es **idempotente**: puede ejecutarse varias veces. Crea los registros que faltan, actualiza los datos modificados y no duplica las definiciones que ya existen.

### Ejecutar la inicialización manualmente

Si solo se había levantado PostgreSQL, pueden aplicarse las migraciones y el seed con:

```bash
docker compose run --rm simulator uv run alembic upgrade head

docker compose run --rm simulator \
  uv run python -m src.storage.seed.seed
```

### Verificar la importación

Revisa primero la salida del seed:

```bash
docker compose logs simulator
```

Después consulta los recuentos directamente en PostgreSQL:

```bash
docker compose exec db sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "SELECT COUNT(*) FROM machines;
      SELECT COUNT(*) FROM alarm_definitions;"'
```

El resultado esperado es:

```text
machines: 5
alarm_definitions: 165
```

Las comillas simples del comando son importantes: hacen que las variables se expandan dentro del contenedor y evitan errores como `role "root" does not exist`.
