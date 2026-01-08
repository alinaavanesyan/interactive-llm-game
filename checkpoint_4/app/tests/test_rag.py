from app.ml.rag_pipeline import rag_forward

if __name__ == "__main__":
    try:
        res = rag_forward(
            question="Bojack is a total jerk",
            character="BoJack"
        )
        print("RESULT:\n", res)
    except Exception as e:
        print("RAG CRASHED:")
        print(type(e).__name__, str(e))
