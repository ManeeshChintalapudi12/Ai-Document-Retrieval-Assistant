from src.schemas import Role, UserContext


ROLE_CLEARANCE_MAP: dict[Role, int] = {
    Role.general: 1,
    Role.engineering: 2,
    Role.finance: 3,
    Role.hr: 4,
    Role.admin: 5,
}

ROLE_DEPARTMENT_MAP: dict[Role, str] = {
    Role.general: "company-wide",
    Role.hr: "hr",
    Role.engineering: "engineering",
    Role.finance: "finance",
    Role.admin: "company-wide",
}


def get_clearance_level(role: str | Role) -> int:
    role_value = Role(role) if not isinstance(role, Role) else role
    return ROLE_CLEARANCE_MAP[role_value]


def build_user_context(user_id: str, role: Role) -> UserContext:
    return UserContext(
        user_id=user_id,
        role=role,
        clearance_level=get_clearance_level(role),
        department=ROLE_DEPARTMENT_MAP[role],
    )
