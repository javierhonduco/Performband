import os
from app import *
import unittest
import tempfile

class SnapAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_snap(self):
        rv = self.app.get('/debug/purchase')
        assert 'transaction' in rv.data
        assert 200 == rv.status_code

    def test_performers(self):
        rv = self.app.get('/performer')
        assert 'all_artists' in rv.data
        assert 'natural' in rv.data
        assert 200 == rv.status_code

    def test_purchase(self):
        rv = self.app.get('/product/1/buy')
        assert 'seller' in rv.data
        assert 200 == rv.status_code

    def test_artist_by_name(self):
        rv = self.app.get('/performer/LOLXDMAFIA')
        assert 'artist_by_nickname' in rv.data
        assert 200 == rv.status_code


    def test_404(self):
        rv = self.app.get('/performer/_asdasd')
        assert 'error_response' in rv.data
        assert 200 != rv.status_code

if __name__ == '__main__':
    unittest.main()
