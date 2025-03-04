import logging
from pathlib import Path
import pandas as pd
import duckdb
import os
from typing import Dict, List, Tuple, Optional
from memories.core.red_hot_memory import RedHotMemory
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

class ColdToRedHot:
    def __init__(self, data_dir: str = None, config_path: str = None):
        """Initialize cold to red-hot transfer manager."""
        self.data_dir = data_dir or os.path.expanduser("~/geo_memories")
        self.red_hot = RedHotMemory(config_path)
        self.con = duckdb.connect(database=':memory:')
        self.con.install_extension("spatial")
        self.con.load_extension("spatial")

    # ... rest of the code remains the same ...
