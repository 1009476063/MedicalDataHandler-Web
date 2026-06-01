"""DICOM Print service — manage printers and send print jobs via DICOM Print SCU."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import pydicom
from pydicom.dataset import Dataset


@dataclass
class PrinterConfig:
    """Configuration for a DICOM Print SCP."""
    id: str
    name: str
    ae_title: str
    host: str
    port: int
    film_size: str = "8X10"
    orientation: str = "PORTRAIT"
    density: int = 15
    max_density: int = 30
    border_density: str = "WHITE"
    empty_image_density: str = "WHITE"
    min_density: int = 0
    trim: str = "NO"


@dataclass
class PrintJob:
    """Tracks a print job status."""
    id: str
    printer_id: str
    status: str = "pending"
    film_size: str = "8X10"
    orientation: str = "PORTRAIT"
    created_at: str = ""


def _printer_to_dict(p: PrinterConfig) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "ae_title": p.ae_title,
        "host": p.host,
        "port": p.port,
        "film_size": p.film_size,
        "orientation": p.orientation,
        "density": p.density,
        "max_density": p.max_density,
        "border_density": p.border_density,
        "empty_image_density": p.empty_image_density,
        "min_density": p.min_density,
        "trim": p.trim,
    }


def _job_to_dict(j: PrintJob) -> dict[str, Any]:
    return {
        "id": j.id,
        "printer_id": j.printer_id,
        "status": j.status,
        "film_size": j.film_size,
        "orientation": j.orientation,
        "created_at": j.created_at,
    }


class PrintService:
    """Manages DICOM printers and print jobs."""

    def __init__(self) -> None:
        self._printers: dict[str, PrinterConfig] = {}
        self._jobs: dict[str, PrintJob] = {}

    def list_printers(self) -> list[PrinterConfig]:
        return list(self._printers.values())

    def get_printer(self, printer_id: str) -> PrinterConfig | None:
        return self._printers.get(printer_id)

    def add_printer(self, config: dict[str, Any]) -> PrinterConfig:
        printer_id = str(uuid.uuid4())
        pc = PrinterConfig(
            id=printer_id,
            name=config.get("name", "Untitled Printer"),
            ae_title=config.get("ae_title", "MEDVISTA"),
            host=config.get("host", "localhost"),
            port=config.get("port", 104),
            film_size=config.get("film_size", "8X10"),
            orientation=config.get("orientation", "PORTRAIT"),
            density=config.get("density", 15),
        )
        self._printers[printer_id] = pc
        return pc

    def update_printer(self, printer_id: str, updates: dict[str, Any]) -> PrinterConfig | None:
        pc = self._printers.get(printer_id)
        if not pc:
            return None
        for key in ("name", "ae_title", "host", "port", "film_size", "orientation", "density"):
            if key in updates:
                setattr(pc, key, updates[key])
        return pc

    def delete_printer(self, printer_id: str) -> bool:
        return self._printers.pop(printer_id, None) is not None

    def send_print(
        self,
        printer_id: str,
        image_data: str,
        options: dict[str, Any] | None = None,
    ) -> PrintJob:
        """Create a print job. Actual DICOM Print SCU transmission would happen here."""
        printer = self._printers.get(printer_id)
        if not printer:
            raise ValueError(f"Printer {printer_id} not found")

        job_id = str(uuid.uuid4())
        opts = options or {}
        job = PrintJob(
            id=job_id,
            printer_id=printer_id,
            status="pending",
            film_size=opts.get("film_size", printer.film_size),
            orientation=opts.get("orientation", printer.orientation),
        )
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> PrintJob | None:
        return self._jobs.get(job_id)


print_service = PrintService()
