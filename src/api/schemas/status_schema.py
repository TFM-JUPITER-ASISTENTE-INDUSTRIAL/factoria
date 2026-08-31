from pydantic import BaseModel

class FactoryStatusResponse(BaseModel):
    total_machines: int
    machines_online: int
    machines_error: int
    active_alarms_count: int