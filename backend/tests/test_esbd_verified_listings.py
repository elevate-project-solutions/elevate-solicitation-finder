import csv
import json
from datetime import datetime
from pathlib import Path

import pytest

from app.collectors.esbd import ESBDCollector

FIXTURES = (
    Path(__file__).resolve
)