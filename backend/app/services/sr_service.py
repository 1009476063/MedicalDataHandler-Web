"""DICOM Structured Reporting (SR) service — parse, create, and manage SR documents."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pydicom
from pydicom.dataset import Dataset


# DICOM SR SOP Class UIDs
_SR_SOP_CLASSES = {
    "1.2.840.10008.5.1.4.1.1.88.33": "Comprehensive SR",
    "1.2.840.10008.5.1.4.1.1.88.22": "Basic Text SR",
    "1.2.840.10008.5.1.4.1.1.88.34": "Comprehensive 3D SR",
    "1.2.840.10008.5.1.4.1.1.88.43": "Key Object Selection",
    "1.2.840.10008.5.1.4.1.1.88.59": "Enhanced SR",
}

# Content relation types
_CONTAINS = "CONTAINS"
_HAS_CONCEPT_MOD = "HAS CONCEPT MOD"
_HAS_OBS_CONTEXT = "HAS OBS CONTEXT"
_INFERRED_FROM = "INFERRED FROM"


@dataclass
class ContentTreeNode:
    """A node in the SR content tree."""
    id: str
    relationship: str
    concept_name: str
    value_type: str
    value: str
    children: list[ContentTreeNode] = field(default_factory=list)


@dataclass
class SrDocument:
    """Represents a parsed or created SR document."""
    id: str
    patient_name: str
    patient_id: str
    study_date: str
    content_date: str
    modality: str
    sr_type: str
    title: str
    institution_name: str
    content_tree: list[ContentTreeNode] = field(default_factory=list)
    file_path: str = ""
    series_uid: str = ""
    sop_instance_uid: str = ""


def _node_to_dict(node: ContentTreeNode) -> dict[str, Any]:
    return {
        "id": node.id,
        "relationship": node.relationship,
        "concept_name": node.concept_name,
        "value_type": node.value_type,
        "value": node.value,
        "children": [_node_to_dict(c) for c in node.children],
    }


def _sr_to_dict(doc: SrDocument) -> dict[str, Any]:
    return {
        "id": doc.id,
        "patient_name": doc.patient_name,
        "patient_id": doc.patient_id,
        "study_date": doc.study_date,
        "content_date": doc.content_date,
        "modality": doc.modality,
        "sr_type": doc.sr_type,
        "title": doc.title,
        "institution_name": doc.institution_name,
        "content_tree": [_node_to_dict(n) for n in doc.content_tree],
        "file_path": doc.file_path,
        "series_uid": doc.series_uid,
        "sop_instance_uid": doc.sop_instance_uid,
    }


def _extract_text_value(dataset: Dataset) -> str:
    """Extract text value from a SR content item dataset."""
    if "TextValue" in dataset:
        return str(dataset.TextValue)
    if "ConceptCodeSequence" in dataset:
        seq = dataset.ConceptCodeSequence
        if seq:
            item = seq[0]
            if "CodeMeaning" in item:
                return str(item.CodeMeaning)
    if "DateValue" in dataset:
        return str(dataset.DateValue)
    if "TimeValue" in dataset:
        return str(dataset.TimeValue)
    if "DateTimeValue" in dataset:
        return str(dataset.DateTimeValue)
    if "NumericValue" in dataset:
        unit = ""
        if "MeasurementUnitsCodeSequence" in dataset:
            useq = dataset.MeasurementUnitsCodeSequence
            if useq and "CodeMeaning" in useq[0]:
                unit = str(useq[0].CodeMeaning)
        return f"{dataset.NumericValue} {unit}".strip()
    return ""


def _extract_concept_name(dataset: Dataset) -> str:
    """Extract concept name from a SR content item dataset."""
    if "ConceptNameCodeSequence" in dataset:
        seq = dataset.ConceptNameCodeSequence
        if seq:
            item = seq[0]
            parts = []
            if "CodeMeaning" in item:
                parts.append(str(item.CodeMeaning))
            if "CodeValue" in item:
                parts.append(f"({item.CodeValue})")
            return " ".join(parts) if parts else "Unknown"
    return "Unknown"


def _parse_content_sequence(
    items: list[Dataset], parent_id: str = ""
) -> list[ContentTreeNode]:
    """Recursively parse a Content Sequence into a tree."""
    nodes: list[ContentTreeNode] = []
    for i, item in enumerate(items):
        node_id = f"{parent_id}.{i}" if parent_id else str(i)
        relationship_type = ""
        if "RelationshipType" in item:
            relationship_type = str(item.RelationshipType)

        value_type = ""
        if "ValueType" in item:
            value_type = str(item.ValueType)

        concept_name = _extract_concept_name(item)
        value = _extract_text_value(item)

        children: list[ContentTreeNode] = []
        if "ContentSequence" in item:
            children = _parse_content_sequence(item.ContentSequence, node_id)

        nodes.append(ContentTreeNode(
            id=node_id,
            relationship=relationship_type,
            concept_name=concept_name,
            value_type=value_type,
            value=value,
            children=children,
        ))
    return nodes


class SrService:
    """Manages DICOM SR documents — parsing, creation, and retrieval."""

    def __init__(self) -> None:
        self._documents: dict[str, SrDocument] = {}  # id → SrDocument
        self._patient_index: dict[str, list[str]] = {}  # patient_id → [doc_ids]
        self._session_index: dict[str, list[str]] = {}  # session_id → [doc_ids]

    def parse_sr_file(self, session_id: str, file_path: str) -> SrDocument:
        """Parse a DICOM SR file and store it."""
        ds = pydicom.dcmread(file_path)
        return self._parse_dataset(session_id, ds, file_path)

    def _parse_dataset(
        self, session_id: str, ds: Dataset, file_path: str = ""
    ) -> SrDocument:
        """Parse a pydicom Dataset into an SrDocument."""
        sop_uid = str(getattr(ds, "SOPInstanceUID", ""))
        series_uid = str(getattr(ds, "SeriesInstanceUID", ""))

        # Determine SR type from SOP Class UID
        sop_class = str(getattr(ds, "SOPClassUID", ""))
        sr_type = _SR_SOP_CLASSES.get(sop_class, "Unknown SR")

        # Extract basic info
        patient_name = str(getattr(ds, "PatientName", "Unknown"))
        patient_id = str(getattr(ds, "PatientID", ""))
        study_date = str(getattr(ds, "StudyDate", ""))
        content_date = str(getattr(ds, "ContentDate", study_date))
        institution = str(getattr(ds, "InstitutionName", ""))

        # Extract document title
        title = ""
        if "ValueTypesCodeSequence" in ds:
            seq = ds.ValueTypesCodeSequence
            if seq and "CodeMeaning" in seq[0]:
                title = str(seq[0].CodeMeaning)
        if not title and "ConceptNameCodeSequence" in ds:
            title = _extract_concept_name(ds)

        # Parse content tree
        content_tree: list[ContentTreeNode] = []
        if "ContentSequence" in ds:
            content_tree = _parse_content_sequence(ds.ContentSequence)

        doc_id = str(uuid.uuid4())
        doc = SrDocument(
            id=doc_id,
            patient_name=patient_name,
            patient_id=patient_id,
            study_date=study_date,
            content_date=content_date,
            modality="SR",
            sr_type=sr_type,
            title=title or sr_type,
            institution_name=institution,
            content_tree=content_tree,
            file_path=file_path,
            series_uid=series_uid,
            sop_instance_uid=sop_uid,
        )

        self._documents[doc_id] = doc
        self._patient_index.setdefault(patient_id, []).append(doc_id)
        self._session_index.setdefault(session_id, []).append(doc_id)
        return doc

    def list_documents(self, session_id: str, patient_id: str = "") -> list[SrDocument]:
        """List SR documents for a session, optionally filtered by patient."""
        doc_ids = self._session_index.get(session_id, [])
        docs = [self._documents[did] for did in doc_ids if did in self._documents]
        if patient_id:
            docs = [d for d in docs if d.patient_id == patient_id]
        return docs

    def get_document(self, doc_id: str) -> SrDocument | None:
        return self._documents.get(doc_id)

    def get_content_tree(self, doc_id: str) -> list[ContentTreeNode]:
        doc = self._documents.get(doc_id)
        return doc.content_tree if doc else []

    def create_from_findings(
        self,
        session_id: str,
        patient_id: str,
        patient_name: str,
        study_date: str,
        findings: list[dict[str, str]],
        template: str = "126000",
        institution: str = "",
    ) -> SrDocument:
        """Create an SR document from AI analysis findings.

        Args:
            patient_id: Patient ID
            patient_name: Patient name
            study_date: Study date (YYYYMMDD)
            findings: List of dicts with 'name', 'value', optional 'description'
            template: SR template code (default: 126000 = Composition)
            institution: Institution name
        """
        now = datetime.now().strftime("%Y%m%d")
        sop_uid = str(uuid.uuid4())
        series_uid = str(uuid.uuid4())

        # Build content tree from findings
        content_tree: list[ContentTreeNode] = []
        for i, finding in enumerate(findings):
            name = finding.get("name", f"Finding {i + 1}")
            value = finding.get("value", "")
            desc = finding.get("description", "")

            # Create a CONTAINS node for each finding
            finding_children = []
            if desc:
                finding_children.append(ContentTreeNode(
                    id=f"{i}.0",
                    relationship=_HAS_CONCEPT_MOD,
                    concept_name="Comment",
                    value_type="TEXT",
                    value=desc,
                ))

            content_tree.append(ContentTreeNode(
                id=str(i),
                relationship=_CONTAINS,
                concept_name=name,
                value_type="NUM" if _is_numeric(value) else "TEXT",
                value=value,
                children=finding_children,
            ))

        doc_id = str(uuid.uuid4())
        doc = SrDocument(
            id=doc_id,
            patient_name=patient_name,
            patient_id=patient_id,
            study_date=study_date,
            content_date=now,
            modality="SR",
            sr_type="Comprehensive SR",
            title="AI Analysis Report",
            institution_name=institution,
            content_tree=content_tree,
            sop_instance_uid=sop_uid,
            series_uid=series_uid,
        )

        self._documents[doc_id] = doc
        self._patient_index.setdefault(patient_id, []).append(doc_id)
        self._session_index.setdefault(session_id, []).append(doc_id)
        return doc

    def delete_document(self, doc_id: str) -> bool:
        doc = self._documents.pop(doc_id, None)
        if not doc:
            return False
        # Clean up indexes
        for session_docs in self._session_index.values():
            if doc_id in session_docs:
                session_docs.remove(doc_id)
        for patient_docs in self._patient_index.values():
            if doc_id in patient_docs:
                patient_docs.remove(doc_id)
        return True


def _is_numeric(value: str) -> bool:
    try:
        float(value.split()[0])
        return True
    except (ValueError, IndexError):
        return False


sr_service = SrService()
