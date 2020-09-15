# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser
import shutil

from FunctionalProfileUtil.FunctionalProfileUtilImpl import FunctionalProfileUtil
from FunctionalProfileUtil.FunctionalProfileUtilServer import MethodContext
from FunctionalProfileUtil.authclient import KBaseAuth as _KBaseAuth

from installed_clients.WorkspaceClient import Workspace
from installed_clients.DataFileUtilClient import DataFileUtil
from FunctionalProfileUtil.Utils.SampleServiceUtil import SampleServiceUtil
from installed_clients.sample_uploaderClient import sample_uploader


class SampleServiceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('FunctionalProfileUtil'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'FunctionalProfileUtil',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = FunctionalProfileUtil(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        suffix = int(time.time() * 1000)
        cls.wsName = "test_ContigFilter_" + str(suffix)
        ret = cls.wsClient.create_workspace({'workspace': cls.wsName})
        cls.wsId = ret[0]

        cls.dfu = DataFileUtil(cls.callback_url)
        cls.sampleservice_util = SampleServiceUtil(cls.cfg)

        cls.sample_id = '80d16006-62ac-4a36-99fe-f5861c4cc8c8'  # pre-saved sample
        cls.sample_uploader = sample_uploader(cls.callback_url, service_ver="dev")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        return self.__class__.wsName

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    def getSampleServiceUtil(self):
        return self.__class__.sampleservice_util

    def loadSampleSet(self):
        if hasattr(self.__class__, 'sample_set_ref'):
            return self.__class__.sample_set_ref

        sample_set_file_name = 'sample_set_test.csv'
        # sample_set_file_name = 'sample_set_test.xls'
        sample_set_file_path = os.path.join(self.scratch, sample_set_file_name)
        shutil.copy(os.path.join('data', sample_set_file_name), sample_set_file_path)

        params = {
            'workspace_name': self.wsName,
            'workspace_id': self.wsId,
            'sample_file': sample_set_file_path,
            'file_format': "SESAR",
            'header_row_index': 2,
            'set_name': 'test1',
            'description': "this is a test sample set."
        }
        import_samples_rec = self.sample_uploader.import_samples(params)

        report_data = self.dfu.get_objects(
                    {"object_refs": [import_samples_rec['report_ref']]})['data'][0]['data']

        sample_set_ref = report_data['objects_created'][0]['ref']

        self.__class__.sample_set_ref = sample_set_ref
        print('Loaded SampleSet: ' + sample_set_ref)
        return sample_set_ref

    def test_get_sample_service_url(self):
        sampleservice_util = self.getSampleServiceUtil()

        ss_url = sampleservice_util.get_sample_service_url()

        print('Getting sample_service URL: {}'.format(ss_url))

        self.assertTrue('SampleService' in ss_url)

    # @unittest.skip("Takes too long")
    def test_get_ids_from_samples(self):
        sampleservice_util = self.getSampleServiceUtil()
        sample_set_ref = self.loadSampleSet()

        data_ids = sampleservice_util.get_ids_from_samples(sample_set_ref)

        sample_names_expected = ['PB-Low-5', 'PB-High-5', 'PB-Low-6', 'PB-High-6', 'PB-Low-7',
                                 'PB-High-7', 'PB-Low-8', 'PB-High-8']

        self.assertCountEqual(data_ids, sample_names_expected)
