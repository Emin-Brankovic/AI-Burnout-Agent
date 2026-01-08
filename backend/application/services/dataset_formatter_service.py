# """
# Dataset Formatter Service.
# Responsibility: Prepare high-quality training datasets from raw feedback.
# """
#
# import csv
# import json
# from datetime import datetime
# from pathlib import Path
# from typing import Dict, Any, List
#
# from backend.domain.repositories_interfaces.agent_prediction_repository_interface import (
#     AgentPredictionRepositoryInterface
# )
# from backend.domain.repositories_interfaces.daily_log_repository_interface import (
#     DailyLogRepositoryInterface
# )
# from backend.domain.entities.agent_prediction import AgentPredictionEntity
# from backend.domain.entities.daily_log import DailyLogEntity
#
#
# Treba se obrisati
# class DatasetFormatterService:
#     MIN_SAMPLES = 5  # hard safety gate
#
#     def __init__(
#         self,
#         prediction_repo: AgentPredictionRepositoryInterface,
#         daily_log_repo: DailyLogRepositoryInterface,
#         dataset_base_path: str = "backend/data"
#     ):
#         self.prediction_repo = prediction_repo
#         self.daily_log_repo = daily_log_repo
#         self.dataset_base_path = Path(dataset_base_path)
#         self.dataset_base_path.mkdir(parents=True, exist_ok=True)
#
#     def generate_dataset(
#         self,
#         since: datetime | None = None,
#         split_ratio: float = 0.8
#     ) -> Dict[str, str]:
#
#         since = since or datetime.min
#
#         print("📊 Fetching validated predictions...")
#         predictions = self.prediction_repo.get_validated_since(since)
#
#         if not predictions:
#             raise ValueError("No validated predictions available for training")
#
#         dataset_rows: List[Dict[str, Any]] = []
#
#         skipped_no_log = 0
#         skipped_invalid = 0
#
#         for pred in predictions:
#             if not pred.human_validation:
#                 skipped_invalid += 1
#                 continue
#
#             log = self.daily_log_repo.get_by_id(pred.daily_log_id)
#             if not log:
#                 skipped_no_log += 1
#                 continue
#
#             row = self._extract_features_and_label(log, pred)
#             dataset_rows.append(row)
#
#         print(f"✅ Dataset rows created: {len(dataset_rows)}")
#         print(f"⚠️ Skipped (no daily log): {skipped_no_log}")
#         print(f"⚠️ Skipped (invalid prediction): {skipped_invalid}")
#
#         if len(dataset_rows) < self.MIN_SAMPLES:
#             raise ValueError(
#                 f"Insufficient training samples: {len(dataset_rows)} "
#                 f"(minimum required: {self.MIN_SAMPLES})"
#             )
#
#         # Dataset versioning
#         version_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
#         version_dir = self.dataset_base_path / version_id
#         version_dir.mkdir(exist_ok=True)
#
#         # Train / Validation split
#         split_index = int(len(dataset_rows) * split_ratio)
#         train_rows = dataset_rows[:split_index]
#         val_rows = dataset_rows[split_index:]
#
#         headers = list(dataset_rows[0].keys())
#
#         train_file = version_dir / "train.csv"
#         val_file = version_dir / "validation.csv"
#         metadata_file = version_dir / "dataset_config.json"
#
#         self._write_csv(train_file, headers, train_rows)
#         self._write_csv(val_file, headers, val_rows)
#
#         metadata = {
#             "version_id": version_id,
#             "created_at": datetime.utcnow().isoformat(),
#             "source_since": since.isoformat() if since != datetime.min else "all",
#             "total_samples": len(dataset_rows),
#             "train_samples": len(train_rows),
#             "val_samples": len(val_rows),
#             "features": headers[:-1],
#             "target": headers[-1],
#         }
#
#         with open(metadata_file, "w") as f:
#             json.dump(metadata, f, indent=2)
#
#         return {
#             "train_file": str(train_file.absolute()),
#             "val_file": str(val_file.absolute()),
#             "metadata_file": str(metadata_file.absolute()),
#         }
#
#     def _extract_features_and_label(
#         self,
#         log: DailyLogEntity,
#         pred: AgentPredictionEntity
#     ) -> Dict[str, Any]:
#         """
#         Feature contract aligned with ModelTrainingService.
#         """
#
#         return {
#             # Required identifiers
#             "Employee_ID": log.employee_id,
#
#             # Core numeric features
#             "hours_worked": log.hours_worked,
#             "hours_slept": log.hours_slept,
#             "motivation_level": log.motivation_level,
#             "stress_level": log.stress_level,
#             "workload_intensity": log.workload_intensity,
#             "overtime_hours": log.overtime_hours_today,
#
#             # Ground-truth label (binary burnout)
#             "is_burnout": 1 if pred.prediction_value == "HIGH" else 0,
#         }
#
#     def _write_csv(
#         self,
#         path: Path,
#         headers: List[str],
#         rows: List[Dict[str, Any]]
#     ):
#         with open(path, "w", newline="") as f:
#             writer = csv.DictWriter(f, fieldnames=headers)
#             writer.writeheader()
#             writer.writerows(rows)
