# Anti-pattern rules

ANTIPATTERNS = {
    "missing_where_delete": lambda q: q.strip().upper().startswith("DELETE") and "WHERE" not in q.upper(),
    "missing_where_update": lambda q: q.strip().upper().startswith("UPDATE") and "WHERE" not in q.upper(),
}