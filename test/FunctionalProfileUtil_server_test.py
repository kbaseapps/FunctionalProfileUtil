# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser
from mock import patch
import json

from FunctionalProfileUtil.FunctionalProfileUtilImpl import FunctionalProfileUtil
from FunctionalProfileUtil.Utils.ProfileImporter import ProfileImporter
from FunctionalProfileUtil.FunctionalProfileUtilServer import MethodContext
from FunctionalProfileUtil.authclient import KBaseAuth as _KBaseAuth

from installed_clients.WorkspaceClient import Workspace
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.FakeObjectsForTestsClient import FakeObjectsForTests

DATA_IDS = ['PB-Low-5', 'PB-High-5', 'PB-Low-6', 'PB-High-6',
            'PB-Low-7', 'PB-High-7', 'PB-Low-8', 'PB-High-8']


class FunctionalProfileUtilTest(unittest.TestCase):

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

        cls.profile_importer = ProfileImporter(cls.cfg)
        cls.dfu = DataFileUtil(cls.callback_url)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def createAnObject(self):
        if hasattr(self.__class__, 'fake_object_ref'):
            return self.__class__.fake_object_ref

        obj_name = 'test_obj.1'
        foft = FakeObjectsForTests(self.callback_url)
        info = foft.create_any_objects({'ws_name': self.wsName, 'obj_names': [obj_name]})[0]

        fake_object_ref = "%s/%s/%s" % (info[6], info[0], info[4])

        self.__class__.fake_object_ref = fake_object_ref
        print('Loaded Fake Object: ' + fake_object_ref)
        return fake_object_ref

    def test_import_func_profile_fail(self):
        fake_object_ref = self.createAnObject()

        with self.assertRaisesRegex(ValueError, "Required keys"):
            self.serviceImpl.import_func_profile(self.ctx, {})

        with self.assertRaisesRegex(ValueError, "Please choose one of"):
            params = {'workspace_id': self.wsId,
                      'func_profile_obj_name': 'test_func_profile',
                      'base_object_ref': fake_object_ref,
                      'profile_file_path': 'profile_file_path',
                      'profile_type': 'fake profile type',
                      'profile_category': 'organism'}
            self.serviceImpl.import_func_profile(self.ctx, params)

        with self.assertRaisesRegex(ValueError, "Please choose community or organism as profile category"):
            params = {'workspace_id': self.wsId,
                      'func_profile_obj_name': 'test_func_profile',
                      'base_object_ref': fake_object_ref,
                      'profile_file_path': 'profile_file_path',
                      'profile_type': 'amplicon',
                      'profile_category': 'fake profile_category'}
            self.serviceImpl.import_func_profile(self.ctx, params)

    def mock_save_objects(params):
        print('Mocking DataFileUtilClient.save_objects')

        obj_data = params['objects'][0]['data']

        return [[obj_data, None, None, None, None, None, None]]

    def mock_get_objects(self, params):
        print('Mocking DataFileUtilClient.get_objects')

        fake_object_ref = params['object_refs'][0]

        obj_data = {'sample_set_ref': fake_object_ref,
                    'col_attributemapping_ref': fake_object_ref,
                    'row_attributemapping_ref': fake_object_ref,
                    'data': {'row_ids': DATA_IDS,
                             'col_ids': DATA_IDS}}

        return {'data': [{'data': obj_data}]}

    @patch.object(DataFileUtil, "save_objects", side_effect=mock_save_objects)
    def test_import_func_profile(self, save_objects):

        data_ids = ['PB-Low-5', 'PB-High-5', 'PB-Low-6', 'PB-High-6',
                    'PB-Low-7', 'PB-High-7', 'PB-Low-8', 'PB-High-8']
        fake_object_ref = self.createAnObject()
        profile_file_path = os.path.join('data', 'func_table.tsv')

        # import community profile
        params = {'workspace_id': self.wsId,
                  'func_profile_obj_name': 'test_func_profile',
                  'base_object_ref': fake_object_ref,
                  'profile_file_path': profile_file_path,
                  'profile_type': 'Amplicon',
                  'profile_category': 'community',
                  'data_epistemology': 'predicted',
                  'epistemology_method': 'FAPROTAX'}
        with patch.object(DataFileUtil, "get_objects", side_effect=self.mock_get_objects):
            func_profile_ref = self.serviceImpl.import_func_profile(self.ctx,
                                                                    params)[0]['func_profile_ref']
            func_profile_data_str = 'null'.join(
                                func_profile_ref.split("None")[1:-1]).strip('/').replace("'", '"')
            func_profile_data = json.loads(func_profile_data_str)

        expected_keys = ['profile_category', 'profile_type',
                         'data_epistemology', 'epistemology_method',
                         'base_object_ref', 'data', 'col_attributemapping_ref']
        self.assertCountEqual(func_profile_data.keys(), expected_keys)

        self.assertEqual(func_profile_data['profile_category'], 'community')
        self.assertEqual(func_profile_data['profile_type'], 'Amplicon')
        self.assertCountEqual(data_ids, func_profile_data['data']['col_ids'])

        # import organism profile
        params = {'workspace_id': self.wsId,
                  'func_profile_obj_name': 'test_func_profile',
                  'base_object_ref': fake_object_ref,
                  'profile_file_path': profile_file_path,  # testing tranpose profile also
                  'profile_type': 'Amplicon',
                  'profile_category': 'organism',
                  'data_epistemology': 'predicted',
                  'epistemology_method': 'FAPROTAX'}
        with patch.object(DataFileUtil, "get_objects", side_effect=self.mock_get_objects):
            func_profile_ref = self.serviceImpl.import_func_profile(self.ctx,
                                                                    params)[0]['func_profile_ref']
            func_profile_data_str = 'null'.join(
                                func_profile_ref.split("None")[1:-1]).strip('/').replace("'", '"')
            func_profile_data = json.loads(func_profile_data_str)

        expected_keys = ['profile_category', 'profile_type',
                         'data_epistemology', 'epistemology_method',
                         'base_object_ref', 'data', 'row_attributemapping_ref']
        self.assertCountEqual(func_profile_data.keys(), expected_keys)

        self.assertEqual(func_profile_data['profile_category'], 'organism')
        self.assertEqual(func_profile_data['profile_type'], 'Amplicon')
        self.assertCountEqual(data_ids, func_profile_data['data']['row_ids'])

        self.assertEqual(func_profile_data['data_epistemology'], 'predicted')
        self.assertEqual(func_profile_data['epistemology_method'], 'FAPROTAX')

        # functional profile table has more items than matrix
        with self.assertRaisesRegex(ValueError, "Matrix column does not"):
            params = {'workspace_id': self.wsId,
                      'func_profile_obj_name': 'test_func_profile',
                      'base_object_ref': fake_object_ref,
                      'profile_file_path': os.path.join('data', 'func_table_extra_col.tsv'),
                      'profile_type': 'Amplicon',
                      'profile_category': 'community',
                      'data_epistemology': 'predicted',
                      'epistemology_method': 'FAPROTAX'}
            with patch.object(DataFileUtil, "get_objects", side_effect=self.mock_get_objects):
                self.serviceImpl.import_func_profile(self.ctx, params)

        with self.assertRaisesRegex(ValueError, "Matrix row does not"):
            params = {'workspace_id': self.wsId,
                      'func_profile_obj_name': 'test_func_profile',
                      'base_object_ref': fake_object_ref,
                      'profile_file_path': os.path.join('data', 'func_table_extra_col.tsv'),
                      'profile_type': 'Amplicon',
                      'profile_category': 'organism',
                      'data_epistemology': 'predicted',
                      'epistemology_method': 'FAPROTAX'}
            with patch.object(DataFileUtil, "get_objects", side_effect=self.mock_get_objects):
                self.serviceImpl.import_func_profile(self.ctx, params)

    def test_import_func_profile_real_test(self):

        data_ids = ['PB-Low-5', 'PB-High-5', 'PB-Low-6', 'PB-High-6',
                    'PB-Low-7', 'PB-High-7', 'PB-Low-8', 'PB-High-8']
        fake_object_ref = self.createAnObject()
        profile_file_path = os.path.join('data', 'func_table_trans.tsv')

        params = {'workspace_id': self.wsId,
                  'func_profile_obj_name': 'test_func_profile',
                  'base_object_ref': fake_object_ref,
                  'profile_file_path': profile_file_path,
                  'profile_type': 'Amplicon',
                  'profile_category': 'organism',
                  'data_epistemology': 'predicted',
                  'epistemology_method': 'FAPROTAX'}

        with patch.object(DataFileUtil, "get_objects", side_effect=self.mock_get_objects):
            func_profile_ref = self.serviceImpl.import_func_profile(
                                                                self.ctx,
                                                                params)[0]['func_profile_ref']

        func_profile_data = self.dfu.get_objects(
                                            {'object_refs': [func_profile_ref]})['data'][0]['data']

        expected_keys = ['profile_category', 'profile_type',
                         'data_epistemology', 'epistemology_method',
                         'base_object_ref', 'data', 'row_attributemapping_ref']
        self.assertCountEqual(func_profile_data.keys(), expected_keys)

        self.assertEqual(func_profile_data['profile_category'], 'organism')
        self.assertEqual(func_profile_data['profile_type'], 'Amplicon')
        self.assertCountEqual(data_ids, func_profile_data['data']['row_ids'])

        self.assertEqual(func_profile_data['data_epistemology'], 'predicted')
        self.assertEqual(func_profile_data['epistemology_method'], 'FAPROTAX')

        # import profile large size
        MB_300 = 300 * 1024 * 1024
        with patch.object(DataFileUtil, "get_objects", side_effect=self.mock_get_objects):
            with patch.object(ProfileImporter, "_calculate_object_size", return_value=MB_300):
                func_profile_ref = self.serviceImpl.import_func_profile(
                                                                    self.ctx,
                                                                    params)[0]['func_profile_ref']

        func_profile_data = self.dfu.get_objects(
                                            {'object_refs': [func_profile_ref]})['data'][0]['data']

        expected_keys = ['profile_category', 'profile_type',
                         'data_epistemology', 'epistemology_method',
                         'base_object_ref', 'data', 'row_attributemapping_ref']
        self.assertCountEqual(func_profile_data.keys(), expected_keys)

        self.assertEqual(func_profile_data['profile_category'], 'organism')
        self.assertEqual(func_profile_data['profile_type'], 'Amplicon')
        self.assertCountEqual(data_ids, func_profile_data['data']['row_ids'])

        self.assertEqual(func_profile_data['data_epistemology'], 'predicted')
        self.assertEqual(func_profile_data['epistemology_method'], 'FAPROTAX')
