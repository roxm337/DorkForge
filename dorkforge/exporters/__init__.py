from dorkforge.exporters.base import Exporter
from dorkforge.exporters.json_exporter import JSONExporter
from dorkforge.exporters.csv_exporter import CSVExporter
from dorkforge.exporters.url_exporter import URLExporter
from dorkforge.exporters.html_exporter import HTMLExporter

__all__ = ["Exporter", "JSONExporter", "CSVExporter", "URLExporter", "HTMLExporter"]

EXPORTER_MAP = {
    "json": JSONExporter,
    "csv": CSVExporter,
    "urls": URLExporter,
    "html": HTMLExporter,
}
