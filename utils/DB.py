import os
import json
import psycopg2
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from Antipatterns.Antipatterns import ANTIPATTERNS

# --- Configuration ---
class Config:
    """Centralized configuration class."""
    DB_BACKEND = os.getenv("SCORER_DB", "postgres")
    POSTGRES_DBNAME = os.getenv("POSTGRES_DBNAME", "scorer")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DBNAME = os.getenv("MONGO_DBNAME", "scorer")

# --- Database Interface ---
class DBInterface:
    """Abstract base class for database clients."""
    def store_results(self, results: list):
        raise NotImplementedError

class PostgresClient(DBInterface):
    """Handles PostgreSQL database connection and basic query execution."""
    def __init__(self, config):
        self.config = config
        self.conn = None

    def __enter__(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.config.POSTGRES_DBNAME,
                user=self.config.POSTGRES_USER,
                password=self.config.POSTGRES_PASSWORD,
                host=self.config.POSTGRES_HOST,
                port=self.config.POSTGRES_PORT
            )
            return self
        except psycopg2.Error as e:
            print(f"Error connecting to PostgreSQL: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def execute_query(self, query: str):
        """Executes a query and returns the results."""
        with self.conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

    def store_results_CI(self, results: list):
        """Stores analysis results in the database."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS query_findings (
                    id SERIAL PRIMARY KEY,
                    file TEXT,
                    query TEXT,
                    findings JSONB
                )
            """)
            for r in results:
                cur.execute(
                    "INSERT INTO query_findings (file, query, findings) VALUES (%s, %s, %s)",
                    (r["file"], r["query"], json.dumps(r["findings"]))
                )
        self.conn.commit()

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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

class MongoClient(DBInterface):
    """Handles MongoDB database operations."""
    def __init__(self, config):
        self.config = config
        self.client = None

    def __enter__(self):
        try:
            self.client = MongoClient(self.config.MONGO_URI, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')  # Test connection
            return self
        except ConnectionFailure as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()

    def store_results(self, results: list):
        db = self.client[self.config.MONGO_DBNAME]
        collection = db["query_findings"]
        collection.insert_many(results)

# --- Factory Function ---
def get_db_client():
    """Factory function to get the correct database client."""
    config = Config()
    if config.DB_BACKEND == "postgres":
        return PostgresClient(config)
    elif config.DB_BACKEND == "mongo":
        return MongoClient(config)
    else:
        raise ValueError("Unsupported database backend.")


