import sys
import os
import subprocess

from nose.tools import assert_equal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from i2b2_import.db_connection import Connection
from i2b2_import.observation_fact_import import csv2db
from i2b2_import.ppmi_meta_import import PPMIMetaImport


DB_URL = 'postgresql://postgres:postgres@localhost:5432/postgres'


class TestFilesRecording:

    def __init__(self):
        self.i2b2_db_conn = None

    @classmethod
    def setup_class(cls):
        subprocess.call("./init_db.sh", shell=True)  # Create the DB tables

    @classmethod
    def teardown_class(cls):
        pass

    def setup(self):
        self.i2b2_db_conn = Connection(DB_URL)

    def teardown(self):
        self.i2b2_db_conn.close()

    def test_csv2db(self):
        csv2db('./data/features/adni.csv', self.i2b2_db_conn, 'TEST')
        assert_equal(self.i2b2_db_conn.db_session.query(self.i2b2_db_conn.ObservationFact).count(), 44)

    def test_ppmi_import(self):
        PPMIMetaImport.meta2i2b2('./data/xml/ppmi.xml', self.i2b2_db_conn)