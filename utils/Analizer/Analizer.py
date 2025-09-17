
from Antipatterns.Antipatterns import ANTIPATTERNS
from utils.Config.Config import *
from utils.Connections.DB import *


class PostgresAnalyzer:
    """Performs analysis using a PostgresClient instance."""
    def __init__(self, client: PostgresClient):
        self.client = client

    # --- Core Logic ---
    def __analyze_sql__(self, sql_text: str):
        """Analyzes SQL for antipatterns."""
        findings = []
        for name, fn in ANTIPATTERNS.items():
            if fn(sql_text):
                findings.append(name)
        return findings


    def analyze_query(self, query: str):
        """
        Performs both antipattern and query plan analysis, safely handling different query types.
        """
        # Step 1: Perform syntactic antipattern matching for all query types
        findings = self.__analyze_sql__(query)

        # Step 2: Only perform query plan analysis for SELECT statements
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            try:
                # Use the client to get the query plan
                plan_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
                raw_plan = self.client.execute_query(plan_query)
                # print("RAW PLAN")
                # print(raw_plan)
                plan = raw_plan[0][0][0]['Plan']
                self._walk_plan(plan, findings)
            except (psycopg2.Error, IndexError, TypeError) as e:
                # If the EXPLAIN command fails (e.g., due to invalid SQL),
                # print the error but continue with syntactic findings.
                print(f"Could not analyze query plan for '{query}': {e}")
                return findings
        else:
            # For non-SELECT queries, just return the syntactic findings
            # and print a note to the user.
            if findings:
                print(f"Note: Antipatterns found in non-SELECT query, skipping query plan analysis.")

        return findings

    def _walk_plan(self, p, findings):
        """Recursively walks the query plan to find antipatterns."""
        node_type = p.get("Node Type", "")
        if node_type == "Seq Scan":
            findings.append("sequential_scan")
        if node_type == "Nested Loop":
            findings.append("nested_loop")
        if "Plans" in p:
            for sub in p["Plans"]:
                self._walk_plan(sub, findings)
