from utils.DB import *
import glob
import sys
from typing import List, Dict

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
                        results.append({
                            "file": file,
                            "query": query,
                            "findings": []
                        })
        except IOError as e:
            print(f"Error reading file {file}: {e}")

    return results

def analyze_queries(db_client, queries: List[Dict]) -> List[Dict]:
    """Analyzes queries using appropriate analyzer based on DB client."""
    if isinstance(db_client, PostgresClient):
        analyzer = PostgresAnalyzer(db_client)
        for result in queries:
            try:
                print("ANALYZING QUERY: ", result['query'])
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
            result['findings'] = [
                name for name, fn in ANTIPATTERNS.items() 
                if fn(result['query'])
            ]
    
    return queries

def print_results(antipatterns: List[Dict]) -> None:
    """Prints analysis results in a formatted way."""
    if antipatterns:
        print("❌ Found anti-patterns:")
        for result in antipatterns:
            print(f"- {result['file']} :: {result['findings']}")
    else:
        print("✅ No anti-patterns found")

def main() -> None:
    """Main function to orchestrate the analysis and storage process."""
    # Read all SQL files
    queries = read_sql_files()
    if not queries:
        print("✅ No SQL queries found to analyze.")
        sys.exit(0)

    exit_code = 0
    try:
        with get_db_client() as db_client:
            # Analyze queries
            analyzed_queries = analyze_queries(db_client, queries)
            
            # Filter queries with findings
            found_antipatterns = [q for q in analyzed_queries if q['findings']]
            
            # Print results
            print_results(found_antipatterns)
            
            # Store results if antipatterns were found
            if found_antipatterns:
                try:
                    db_client.store_results_CI(found_antipatterns)
                    print("Results stored successfully.")
                    exit_code = 1  # Fail CI
                except Exception as store_error:
                    print(f"Warning: Failed to store results: {store_error}")
                    if hasattr(db_client, 'connection'):
                        db_client.connection.rollback()
                    exit_code = 1

    except Exception as e:
        print(f"An error occurred: {e}")
        exit_code = 1

    sys.exit(exit_code)

if __name__ == "__main__":
    main()