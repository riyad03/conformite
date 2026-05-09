from dotenv import load_dotenv
load_dotenv()

from conformite.runner import run_batch

run_batch(
    procedures_dir="Procédures test",
    referentiel_path="Requirement 09-08.xlsx",
)
