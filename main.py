from dotenv import load_dotenv
load_dotenv()  

from app.runner import run_pipeline

if __name__ == "__main__":
    run_pipeline()
