# FactorIA 🏭

FactorIA es una plataforma industrial en Python que simula una planta de producción, persiste su estado en PostgreSQL y ofrece una API REST con FastAPI para consultar máquinas, sensores, catálogo de fallos y ocurrencias de alarma.

El proyecto sigue una separación por capas inspirada en Clean Architecture y DDD:

- `domain`: máquinas, PLC, sensores y alarmas sin dependencias de HTTP.
- `services`: casos de uso, como activar o resolver una alarma.
- `storage`: modelos SQLAlchemy, repositorios, importadores y seed.
- `api`: rutas FastAPI y schemas Pydantic.
- `alembic`: evolución versionada del esquema PostgreSQL.

## Estado actual

Los cinco CSV versionados en `data/alarm_catalogs/` producen:

| Recurso | Cantidad |
| --- | ---: |
| Máquinas | 5 |
| PLC | 5 |
| Sensores agrupados | 81 |
| Definiciones de alarma | 165 |

El simulador genera una nueva ocurrencia válida cada 10 segundos. Para ello vuelve a leer el estado de PostgreSQL, elige un sensor con fallos disponibles y selecciona una de sus definiciones no activas. La API permite consultar y resolver las ocurrencias.

## Sensores obtenidos del catálogo

Los sensores ya no se clasifican mediante una lista manual de tipos neumáticos, eléctricos o software. El importador obtiene `sensor_type` del penúltimo segmento de `tag_id`:

```python
sensor_type = tag_id.split(".")[-2]
```

Ejemplos:

| `tag_id` | `sensor_type` |
| --- | --- |
| `PONTIA.LACO01.DENE01.STACK.LEVEL_LOW` | `STACK` |
| `PONTIA.LACO01.DENE01.STACK.EMPTY` | `STACK` |
| `PONTIA.LACO01.DENE01.AXIS_Z.SERVO_FAULT` | `AXIS_Z` |
| `PONTIA.LACO01.ENCA01.ROBOT.COLLISION_DETECTED` | `ROBOT` |

`sensor_id` es la clave numérica asignada por PostgreSQL. Un mismo tipo en máquinas diferentes tiene IDs distintos porque la agrupación se realiza por `PLC + sensor_type`.

Por ejemplo, el sensor `STACK` de Denester tiene un único `sensor_id` y estas definiciones:

- `DEN-0004`: `STACK.LEVEL_LOW`.
- `DEN-0005`: `STACK.EMPTY`.
- `DEN-0021`: `STACK.CHAIN_WEAR_DETECTED`.

El número de sensores por máquina es:

| Máquina | ID externo | Sensores | Definiciones |
| --- | --- | ---: | ---: |
| Denester | `DENESTER-01` | 15 | 30 |
| Encajadora | `ENCAJADORA-01` | 16 | 30 |
| Estuchadora | `ESTUCHADORA-01` | 19 | 35 |
| Serializadora | `SERIALIZADORA-01` | 14 | 35 |
| Termoformadora | `TERMOFORMADORA-01` | 17 | 35 |
| **Total** |  | **81** | **165** |

## Flujo de una alarma

```text
CSV
 ↓
Machine → PLC → Sensor agrupado → AlarmDefinition
                                  ↓
App selecciona un fallo disponible cada 10 s
                                  ↓
AlarmEventService valida máquina, sensor, código y tag
                                  ↓
Alarm ACTIVE guardada en PostgreSQL
                                  ↓
API consulta o resuelve mediante PATCH
```

`alarm_definitions` y `alarms` representan conceptos diferentes:

- `alarm_definitions` es el catálogo de fallos posibles.
- `alarms` es el histórico de las veces que esos fallos ocurrieron.

Una definición puede tener muchas ocurrencias históricas, pero PostgreSQL impide que existan dos ocurrencias activas simultáneas de la misma definición. Al resolver una alarma se conserva el registro con estado `SOLVED` y `resolved_at`; la misma definición puede volver a ocurrir más adelante con otro `alarm_id`.

## Modelo de datos

```mermaid
erDiagram
    machines ||--|| plcs : tiene
    plcs ||--o{ sensors : contiene
    machines ||--o{ alarm_definitions : cataloga
    sensors ||--o{ alarm_definitions : agrupa
    alarm_definitions ||--o{ alarms : origina
    machines ||--o{ alarms : registra
    sensors ||--o{ alarms : detecta

    machines {
        integer id PK
        string external_id UK
        string name UK
    }
    plcs {
        integer id PK
        integer owner_id FK
    }
    sensors {
        integer id PK
        integer owner_id FK
        string name
        string sensor_type
        string tag_id "compatibilidad"
        varchar_array error_codes
        float failure_probability
    }
    alarm_definitions {
        integer id PK
        string external_alarm_id UK
        integer machine_id FK
        integer sensor_id FK
        string alarm_code
        string alarm_name
        string tag_id
        string component
        string severity
    }
    alarms {
        integer id PK
        integer machine_id FK
        integer sensor_id FK
        integer alarm_definition_id FK
        string error_code
        string status
        timestamp triggered_at
        timestamp resolved_at
        jsonb raw_payload
    }
```

La restricción `UNIQUE(owner_id, sensor_type)` garantiza un solo grupo del mismo tipo dentro de cada PLC. La identidad de negocio de una definición se protege con `UNIQUE(machine_id, alarm_code)` y `external_alarm_id` también es único.

## API REST

Con el proyecto arrancado:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/status` | Contadores globales de máquinas y alarmas activas. |
| `GET` | `/machines` | Máquinas con PLC, sensores, definiciones y errores activos. |
| `GET` | `/machines/{machine_id}` | Detalle de una máquina por su ID interno. |
| `GET` | `/alarm-definitions` | Catálogo; admite `machine_id` y `sensor_id`. |
| `GET` | `/alarms` | Ocurrencias; admite `status` y `machine_id`. |
| `GET` | `/alarms/{alarm_id}` | Detalle enriquecido de una ocurrencia. |
| `PATCH` | `/alarms/{alarm_id}/resolve` | Cambia una ocurrencia a `SOLVED`. |

Las respuestas de alarmas incluyen máquina, sensor, `sensor_type`, definición, código, nombre, tag, componente, severidad y fechas.

Si Docker se ejecuta en una máquina remota mediante SSH, `localhost` en el navegador apunta al equipo local. En ese caso utiliza el hostname o IP del servidor, por ejemplo `http://luis-hp:8000/docs`, o reenvía el puerto 8000 desde la pestaña **Ports** de VS Code.

## Arranque con Docker Compose

### 1. Configuración

```bash
cp .env.example .env
```

Variables necesarias:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=factoria
```

No subas `.env` al repositorio.

### 2. Arrancar todo

```bash
docker compose up --build -d
```

Servicios:

- `db` (`factoria_db`): PostgreSQL 16 con volumen persistente y healthcheck.
- `simulator` (`factoria_app`): aplica migraciones, ejecuta el seed e inicia la simulación.
- `api` (`factoria_api`): expone FastAPI en el puerto 8000.

El simulador ejecuta:

```text
alembic upgrade head
        ↓
python -m src.storage.seed.seed
        ↓
python main.py
```

La API espera a que PostgreSQL esté saludable. Durante una primera construcción puede necesitar unos segundos adicionales mientras el simulador termina las migraciones y la importación.

### 3. Comprobar servicios y logs

```bash
docker compose ps -a
docker compose logs --tail=100 simulator
docker compose logs -f api
docker compose logs -f simulator
```

Un seed repetido y sin cambios debe mostrar:

```text
machines_created: 0
sensors_created: 0
definitions_created: 0
definitions_updated: 0
definitions_unchanged: 165
```

### 4. Detener conservando PostgreSQL

```bash
docker compose down
```

Para eliminar también el volumen y reconstruir desde cero:

```bash
docker compose down -v
```

> `down -v` elimina todo el contenido de PostgreSQL. Úsalo únicamente cuando quieras borrar deliberadamente los datos.

## Comprobación funcional mediante la API

```bash
curl http://127.0.0.1:8000/status
curl http://127.0.0.1:8000/machines
curl http://127.0.0.1:8000/alarm-definitions
curl "http://127.0.0.1:8000/alarms?status=ACTIVE"
```

Para resolver una ocurrencia, utiliza el `alarm_id` obtenido en `/alarms`:

```bash
curl -X PATCH http://127.0.0.1:8000/alarms/20/resolve
```

Después vuelve a consultar la máquina y `/status`. El código resuelto debe desaparecer de `current_errors`; la máquina solo estará `ONLINE` si no tiene ninguna otra alarma activa.

## Migraciones y seed manuales

El `head` actual de Alembic es `e83b6a912d04`.

```bash
docker compose run --rm simulator uv run alembic current
docker compose run --rm simulator uv run alembic upgrade head
docker compose run --rm simulator uv run python -m src.storage.seed.seed
```

Validar el catálogo sin conservar cambios:

```bash
docker compose run --rm simulator \
  uv run python -m src.storage.importers.alarm_catalog_importer \
  data/alarm_catalogs --dry-run
```

El importador es transaccional e idempotente: valida todos los CSV antes de confirmar, crea los registros ausentes, actualiza los modificados y no duplica los existentes.

## Desarrollo local

Requisitos:

- Python 3.12 o superior.
- `uv`.
- PostgreSQL accesible mediante `DATABASE_URL`.

Con PostgreSQL de Docker activo:

```bash
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/factoria"
uv run alembic upgrade head
uv run python -m src.storage.seed.seed
uv run uvicorn src.api.main:app --reload --port 8000
```

En otra terminal, para ejecutar el simulador:

```bash
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/factoria"
uv run main.py
```

## Pruebas y CI

La suite contiene 34 pruebas unitarias y no necesita una DDBB. Comprueba:

- Contrato de los cinco CSV.
- 165 definiciones y 81 grupos.
- Códigos `STACK` de Denester.
- Extracción y validación de `sensor_type`.
- Selección de fallos asociados y todavía no activos.
- Activación, deduplicación, validación y resolución.
- Intervalo del simulador sin esperas reales.
- Recarga del estado después de una resolución externa.
- Configuración de relaciones SQLAlchemy.

Ejecución equivalente al workflow de GitHub Actions:

```bash
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/factoria_test" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONPATH=. \
uv run pytest -q
```

La URL es necesaria para construir el engine durante los imports. Las pruebas usan dobles y no intentan conectarse a ella. El workflow `.github/workflows/ci.yml` ejecuta la suite en cada pull request.

La comprobación de PostgreSQL se realiza funcionalmente arrancando Docker y consultando la API, separada del CI unitario.

## Estructura principal

```text
factoria/
├── .github/workflows/ci.yml
├── alembic/versions/
├── data/alarm_catalogs/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── alarm_definitions.py
│   │   │   ├── alarms.py
│   │   │   ├── machines.py
│   │   │   └── status.py
│   │   └── schemas/
│   ├── domain/
│   │   ├── alarm.py
│   │   ├── alarm_definition.py
│   │   ├── machine.py
│   │   ├── plc.py
│   │   └── sensor.py
│   ├── services/alarm_event_service.py
│   ├── storage/
│   │   ├── connectors/postgresql.py
│   │   ├── entities/
│   │   ├── importers/alarm_catalog_importer.py
│   │   ├── repositories/
│   │   └── seed/seed.py
│   └── app.py
├── tests/
├── docker-compose.yml
├── Dockerfile
├── main.py
└── pyproject.toml
```

## Limitaciones actuales

- Los CSV incluyen instrucciones de seguridad, resolución, reset, validación y perfil requerido, pero todavía no se persisten en PostgreSQL.
- El simulador representa señales lógicas y no se comunica todavía con un PLC, MQTT u OPC-UA real.
- Solo se admiten las severidades `ERROR` y `CRITICAL_ERROR` definidas por el importador.
- El seed no elimina ni desactiva automáticamente una definición retirada de un CSV.
- La API no tiene autenticación ni autorización.
- Migraciones y seed todavía se ejecutan dentro del servicio `simulator`; no existe un servicio Compose de inicialización independiente.
