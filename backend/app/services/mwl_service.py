"""DICOM Modality Worklist (MWL) service — local CSV and remote DICOMweb query."""

import csv
import io
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional

import httpx


@dataclass
class MwlItem:
    id: str = ""
    patient_name: str = ""
    patient_id: str = ""
    accession_number: str = ""
    study_date: str = ""
    modality: str = ""
    referring_physician: str = ""
    scheduled_step_status: str = ""
    study_instance_uid: str = ""
    scheduled_station_ae_title: str = ""
    requested_procedure_description: str = ""
    institution_name: str = ""
    station_name: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


class MwlService:
    """In-memory MWL with CSV import/export and remote DICOMweb query."""

    def __init__(self):
        self.worklists: dict[str, list[MwlItem]] = {}  # session_id → items

    def _get_items(self, session_id: str) -> list[MwlItem]:
        return self.worklists.setdefault(session_id, [])

    def import_csv(self, session_id: str, csv_data: str) -> list[MwlItem]:
        reader = csv.DictReader(io.StringIO(csv_data))
        items = []
        for row in reader:
            item = MwlItem(
                patient_name=row.get("PatientName", ""),
                patient_id=row.get("PatientID", ""),
                accession_number=row.get("AccessionNumber", ""),
                study_date=row.get("StudyDate", ""),
                modality=row.get("Modality", ""),
                referring_physician=row.get("ReferringPhysicianName", ""),
                scheduled_step_status=row.get("ScheduledProcedureStepStatus", ""),
                study_instance_uid=row.get("StudyInstanceUID", ""),
                scheduled_station_ae_title=row.get("ScheduledStationAETitle", ""),
                requested_procedure_description=row.get("RequestedProcedureDescription", ""),
                institution_name=row.get("InstitutionName", ""),
                station_name=row.get("StationName", ""),
            )
            items.append(item)
        self.worklists[session_id] = items
        return items

    def export_csv(self, session_id: str) -> str:
        items = self._get_items(session_id)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "PatientName", "PatientID", "AccessionNumber", "StudyDate",
            "Modality", "ReferringPhysicianName", "ScheduledProcedureStepStatus",
            "StudyInstanceUID", "ScheduledStationAETitle",
            "RequestedProcedureDescription", "InstitutionName", "StationName",
        ])
        writer.writeheader()
        for item in items:
            writer.writerow({
                "PatientName": item.patient_name,
                "PatientID": item.patient_id,
                "AccessionNumber": item.accession_number,
                "StudyDate": item.study_date,
                "Modality": item.modality,
                "ReferringPhysicianName": item.referring_physician,
                "ScheduledProcedureStepStatus": item.scheduled_step_status,
                "StudyInstanceUID": item.study_instance_uid,
                "ScheduledStationAETitle": item.scheduled_station_ae_title,
                "RequestedProcedureDescription": item.requested_procedure_description,
                "InstitutionName": item.institution_name,
                "StationName": item.station_name,
            })
        return output.getvalue()

    def search_local(self, session_id: str, query: str) -> list[MwlItem]:
        items = self._get_items(session_id)
        if not query:
            return items
        q = query.lower()
        return [
            i for i in items
            if q in i.patient_name.lower()
            or q in i.patient_id.lower()
            or q in i.accession_number.lower()
            or q in i.referring_physician.lower()
            or q in i.requested_procedure_description.lower()
        ]

    def add_item(self, session_id: str, item: MwlItem) -> MwlItem:
        self._get_items(session_id).append(item)
        return item

    def update_item(self, session_id: str, item_id: str, updates: dict) -> MwlItem:
        items = self._get_items(session_id)
        for item in items:
            if item.id == item_id:
                for k, v in updates.items():
                    if hasattr(item, k):
                        setattr(item, k, v)
                return item
        raise KeyError(f"Item {item_id} not found")

    def delete_item(self, session_id: str, item_id: str) -> bool:
        items = self._get_items(session_id)
        before = len(items)
        self.worklists[session_id] = [i for i in items if i.id != item_id]
        return len(self.worklists[session_id]) < before


mwl_service = MwlService()
