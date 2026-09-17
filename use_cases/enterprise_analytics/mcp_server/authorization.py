from use_cases.enterprise_analytics.schemas import AnalyticsDomain


DEMO_ENTITLEMENTS: dict[str, set[AnalyticsDomain]] = {
    "demo-finance-user": {AnalyticsDomain.FINANCE},
    "demo-analyst": {
        AnalyticsDomain.FINANCE,
        AnalyticsDomain.OPERATIONS,
    },
    "demo-unauthorized-user": set(),
}


def get_allowed_domains(user_id: str) -> set[AnalyticsDomain]:
    return set(DEMO_ENTITLEMENTS.get(user_id, set()))


def require_domains(
    user_id: str,
    required_domains: set[AnalyticsDomain],
) -> None:
    allowed = get_allowed_domains(user_id)
    missing = required_domains - allowed
    if missing:
        names = ", ".join(sorted(domain.value for domain in missing))
        raise PermissionError(
            f"User {user_id!r} is not authorized for: {names}"
        )