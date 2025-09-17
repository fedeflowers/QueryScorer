from utils.Connections.DB import get_db_client, PostgresClient
from utils.Analizer.Analizer import PostgresAnalyzer
from utils.Config.Config import Config
import glob
import sys
from typing import List, Dict

# --- Helper Functions (as they were) ---

def read_sql_files() -> List[Dict]:
    """Reads all SQL files and returns a list of file/query pairs."""
    results = []
    for file in glob.glob("**/*.sql", recursive=True):
        try:
            with open(file, 'r') as f:
                queries = f.read().split(";")
                for query in queries:
                    query = query.strip()
                    if query:
                        results.append({"file": file, "query": query, "findings": []})
        except IOError as e:
            print(f"Error reading file {file}: {e}")
    return results

def analyze_queries(db_client, queries: List[Dict]) -> List[Dict]:
    """Analyzes queries using appropriate analyzer based on DB client."""
    if isinstance(db_client, PostgresClient):
        analyzer = PostgresAnalyzer(db_client)
        for result in queries:
            try:
                result['findings'] = analyzer.analyze_query(result['query'])
            except Exception as e:
                print(f"Warning: Could not analyze query in {result['file']}: {e}")
                result['findings'] = []
                # Ensure transaction is still valid
                if hasattr(db_client, 'connection'):
                    db_client.connection.rollback()
    else:
        # Fallback to simple analysis for other backends
        from Antipatterns.Antipatterns import ANTIPATTERNS
        for result in queries:
            result['findings'] = [name for name, fn in ANTIPATTERNS.items() if fn(result['query'])]
    return queries

def print_results(antipatterns: List[Dict]) -> None:
    """Prints analysis results in a formatted way."""
    if antipatterns:
        print("❌ Found anti-patterns:")
        for result in antipatterns:
            print(f"- {result['file']} :: {result['findings']}")
    else:
        print("✅ No anti-patterns found")

# --- The Test Function ---

def test_sql_antipatterns() -> bool:
    """
    Main test function for the CI pipeline.
    Returns True if no antipatterns are found, False otherwise.
    """
    queries = read_sql_files()
    if not queries:
        print("✅ No SQL queries found to analyze.")
        return True

    try:
        with get_db_client() as db_client:
            analyzed_queries = analyze_queries(db_client, queries)
            found_antipatterns = [q for q in analyzed_queries if q['findings']]
            
            print_results(found_antipatterns)

            if found_antipatterns:
                try:
                    db_client.store_results_CI(found_antipatterns)
                    print("Results stored successfully.")
                except Exception as store_error:
                    print(f"Warning: Failed to store results: {store_error}")
                    if hasattr(db_client, 'connection'):
                        db_client.connection.rollback()
                return False  # Test fails
            else:
                return True  # Test passes

    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        return False # Test fails

# --- Entry Point for CI ---

if __name__ == "__main__":
    if test_sql_antipatterns():
        sys.exit(0)  # Exit code 0 means success
    else:
        sys.exit(1)  # Exit code 1 means failure