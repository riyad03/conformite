from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Absolute project root — works regardless of where the script is invoked from
PROJECT_ROOT = Path(__file__).parent.parent
RAPPORTS_DIR = PROJECT_ROOT / "rapports"


def _default_report_metadata() -> dict:
    return {
        "client":              "M2T / STAREO",
        "autorite_emettrice":  "CNDP — Commission Nationale de contrôle de la Protection des Données à caractère Personnel",
        "reference":           "Loi n° 09-08 relative à la protection des personnes physiques à l'égard du traitement des données à caractère personnel",
        "intitule":            "Loi 09-08 — Protection des données à caractère personnel",
        "entree_en_vigueur":   "18/02/2009",
        "echeance_conformite": "31/12/2026",
        "date_publication":    "18/02/2009",
    }


@dataclass
class AppConfig:
    procedures_dir: str      = str(PROJECT_ROOT / "Procédures test")
    referentiel_path: str    = str(PROJECT_ROOT / "Requirement 09-08.xlsx")
    max_eval_iterations: int = 3
    report_metadata: dict    = field(default_factory=_default_report_metadata)
