import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="dossier-test-")
os.environ["EXTRACTION_PROVIDER"] = "fake"
os.environ["LIVE_EXTRACTION"] = "0"
