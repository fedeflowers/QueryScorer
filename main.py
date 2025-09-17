from utils.utils import *
from Antipatterns.Antipatterns import *

import  glob, sys

def main():
    results = []
    for file in glob.glob("**/*.sql", recursive=True):
        with open(file) as f:
            queries = f.read().split(";")
            for q in queries:
                q = q.strip()
                if not q:
                    continue
                findings = analyze_sql(q)
                if findings:
                    results.append({"file": file, "query": q, "findings": findings})
    
    if results:
        print("❌ Found anti-patterns:")
        for r in results:
            print(f"- {r['file']} :: {r['findings']}")
        try:
            with get_db_client() as db_client: # Uses __enter__ and __exit__ methods: pattern = context manager
                db_client.store_results(results)
            print("Results stored successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")
        sys.exit(1)  # fail CI
    else:
        print("✅ No anti-patterns found")

if __name__ == "__main__":
    main()
