# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser
from mock import patch
import json

from FunctionalProfileUtil.FunctionalProfileUtilImpl import FunctionalProfileUtil
from FunctionalProfileUtil.Utils.ProfileImporter import ProfileImporter
from FunctionalProfileUtil.Utils.SampleServiceUtil import SampleServiceUtil
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

    def test__build_profile_data(self):

        data_ids = ['PB-Low-5', 'PB-High-5', 'PB-Low-6', 'PB-High-6',
                    'PB-Low-7', 'PB-High-7', 'PB-Low-8', 'PB-High-8']
        profile_file_path = os.path.join('data', 'func_table.tsv')

        # invalide data_epistemology
        with self.assertRaisesRegex(ValueError, "Data epistemology can only be one of"):
            profiles = {'pathway': {'data_epistemology': 'a'}}
            self.profile_importer._build_profile_data(profiles, data_ids)

        # unmatched ids
        with self.assertRaisesRegex(ValueError, "Profile file does not contain all data"):
            profiles = {'pathway': {'data_epistemology': 'predicted',
                                    'epistemology_method': 'FAPROTAX',
                                    'profile_file_path': profile_file_path}}
            self.profile_importer._build_profile_data(profiles, ['unmatched_id'])

        # sccussfully build pathway profile
        profiles = {'pathway': {'data_epistemology': 'predicted',
                                'epistemology_method': 'FAPROTAX',
                                'profile_file_path': profile_file_path}}
        gen_profile_data = self.profile_importer._build_profile_data(profiles, data_ids)

        self.assertCountEqual(gen_profile_data.keys(), ['pathway'])
        self.assertEqual(gen_profile_data['pathway']['data_epistemology'], 'predicted')
        self.assertEqual(gen_profile_data['pathway']['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(gen_profile_data['pathway']['description'])
        self.assertCountEqual(data_ids,
                              gen_profile_data['pathway']['profile_data']['col_ids'])

        # sccussfully build custom profile
        profiles = {'function': {'data_epistemology': 'predicted',
                                 'epistemology_method': 'FAPROTAX',
                                 'profile_file_path': profile_file_path}}
        gen_profile_data = self.profile_importer._build_profile_data(profiles, data_ids)

        self.assertCountEqual(gen_profile_data.keys(), ['custom_profiles'])

        self.assertCountEqual(gen_profile_data.keys(), ['custom_profiles'])
        self.assertCountEqual(gen_profile_data['custom_profiles'].keys(), ['function'])
        self.assertEqual(gen_profile_data['custom_profiles']['function']['data_epistemology'],
                         'predicted')
        self.assertEqual(gen_profile_data['custom_profiles']['function']['epistemology_method'],
                         'FAPROTAX')
        self.assertIsNone(gen_profile_data['custom_profiles']['function']['description'])
        self.assertCountEqual(
                        data_ids,
                        gen_profile_data['custom_profiles']['function']['profile_data']['col_ids'])

        # sccussfully detect profile is transposed
        profiles = {'pathway': {'data_epistemology': 'predicted',
                                'epistemology_method': 'FAPROTAX',
                                'profile_file_path': os.path.join('data', 'func_table_trans.tsv')}}
        gen_profile_data = self.profile_importer._build_profile_data(profiles, data_ids)

        self.assertCountEqual(gen_profile_data.keys(), ['pathway'])
        self.assertEqual(gen_profile_data['pathway']['data_epistemology'], 'predicted')
        self.assertEqual(gen_profile_data['pathway']['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(gen_profile_data['pathway']['description'])
        self.assertCountEqual(data_ids,
                              gen_profile_data['pathway']['profile_data']['col_ids'])

    def test_import_func_profile_fail(self):
        with self.assertRaisesRegex(ValueError, "Required keys"):
            self.serviceImpl.import_func_profile(self.ctx, {})

        with self.assertRaisesRegex(ValueError, "Missing sample_set_ref from community profile"):
            params = {'workspace_id': self.wsId,
                      'func_profile_obj_name': 'test_func_profile',
                      'original_matrix_ref': '1/1/1',
                      'community_profile': {'profiles': {}}}
            self.serviceImpl.import_func_profile(self.ctx, params)

        with self.assertRaisesRegex(ValueError, "Missing amplicon_set_ref from organism profile"):
            params = {'workspace_id': self.wsId,
                      'func_profile_obj_name': 'test_func_profile',
                      'original_matrix_ref': '1/1/1',
                      'organism_profile': {'profiles': {}}}
            self.serviceImpl.import_func_profile(self.ctx, params)

    def mock_save_objects(params):
        print('Mocking DataFileUtilClient.save_objects')

        obj_data = params['objects'][0]['data']

        return [[obj_data, None, None, None, None, None, None]]

    @patch.object(SampleServiceUtil, "get_ids_from_samples", return_value=DATA_IDS)
    @patch.object(ProfileImporter, "_get_ids_from_amplicon_set", return_value=DATA_IDS)
    @patch.object(DataFileUtil, "save_objects", side_effect=mock_save_objects)
    def test_import_func_profile(self, get_ids_from_samples, _get_ids_from_amplicon_set, save_objects):

        data_ids = ['PB-Low-5', 'PB-High-5', 'PB-Low-6', 'PB-High-6',
                    'PB-Low-7', 'PB-High-7', 'PB-Low-8', 'PB-High-8']
        profile_file_path = os.path.join('data', 'func_table.tsv')

        # import community profile only
        params = {'workspace_id': self.wsId,
                  'func_profile_obj_name': 'test_func_profile',
                  'original_matrix_ref': '1/1/1',
                  'community_profile': {'sample_set_ref': '1/1/1',
                                        'profiles': {'pathway': {'data_epistemology': 'predicted',
                                                                 'epistemology_method': 'FAPROTAX',
                                                                 'profile_file_path': profile_file_path}}}}
        func_profile_ref = self.serviceImpl.import_func_profile(self.ctx, params)[0]['func_profile_ref']

        func_profile_data_str = 'null'.join(func_profile_ref.split("None")[1:-1]).strip('/').replace("'", '"')
        func_profile_data = json.loads(func_profile_data_str)

        self.assertCountEqual(func_profile_data.keys(), ['original_matrix_ref', 'community_profile'])
        community_profile = func_profile_data['community_profile']

        self.assertCountEqual(community_profile.keys(), ['pathway', 'sample_set_ref'])
        self.assertEqual(community_profile['sample_set_ref'], '1/1/1')
        pathway_profile = community_profile['pathway']

        self.assertCountEqual(pathway_profile.keys(), ['data_epistemology', 'epistemology_method',
                                                       'description', 'profile_data'])
        self.assertEqual(pathway_profile['data_epistemology'], 'predicted')
        self.assertEqual(pathway_profile['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(pathway_profile['description'])
        self.assertCountEqual(data_ids,
                              pathway_profile['profile_data']['col_ids'])

        # import organism profile only
        params = {'workspace_id': self.wsId,
                  'func_profile_obj_name': 'test_func_profile',
                  'original_matrix_ref': '1/1/1',
                  'organism_profile': {'amplicon_set_ref': '1/1/1',
                                       'profiles': {'EC': {'data_epistemology': 'predicted',
                                                           'epistemology_method': 'FAPROTAX',
                                                           'profile_file_path': profile_file_path}}}}
        func_profile_ref = self.serviceImpl.import_func_profile(self.ctx, params)[0]['func_profile_ref']

        func_profile_data_str = 'null'.join(func_profile_ref.split("None")[1:-1]).strip('/').replace("'", '"')
        func_profile_data = json.loads(func_profile_data_str)

        self.assertCountEqual(func_profile_data.keys(), ['original_matrix_ref', 'organism_profile'])
        organism_profile = func_profile_data['organism_profile']

        self.assertCountEqual(organism_profile.keys(), ['EC', 'amplicon_set_ref'])
        self.assertEqual(organism_profile['amplicon_set_ref'], '1/1/1')
        EC_profile = organism_profile['EC']

        self.assertCountEqual(EC_profile.keys(), ['data_epistemology', 'epistemology_method',
                                                  'description', 'profile_data'])
        self.assertEqual(EC_profile['data_epistemology'], 'predicted')
        self.assertEqual(EC_profile['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(EC_profile['description'])
        self.assertCountEqual(data_ids,
                              EC_profile['profile_data']['col_ids'])

        # import community profile and organism profile
        params = {'workspace_id': self.wsId,
                  'func_profile_obj_name': 'test_func_profile',
                  'original_matrix_ref': '1/1/1',
                  'community_profile': {'sample_set_ref': '1/1/1',
                                        'profiles': {'pathway': {'data_epistemology': 'predicted',
                                                                 'epistemology_method': 'FAPROTAX',
                                                                 'profile_file_path': profile_file_path}}},
                  'organism_profile': {'amplicon_set_ref': '1/1/1',
                                       'profiles': {'EC': {'data_epistemology': 'predicted',
                                                           'epistemology_method': 'FAPROTAX',
                                                           'profile_file_path': profile_file_path}}}}
        func_profile_ref = self.serviceImpl.import_func_profile(self.ctx, params)[0]['func_profile_ref']

        func_profile_data_str = 'null'.join(func_profile_ref.split("None")[1:-1]).strip('/').replace("'", '"')
        func_profile_data = json.loads(func_profile_data_str)

        self.assertCountEqual(func_profile_data.keys(), ['original_matrix_ref',
                                                         'community_profile',
                                                         'organism_profile'])
        organism_profile = func_profile_data['organism_profile']
        community_profile = func_profile_data['community_profile']

        self.assertCountEqual(organism_profile.keys(), ['EC', 'amplicon_set_ref'])
        self.assertEqual(organism_profile['amplicon_set_ref'], '1/1/1')
        EC_profile = organism_profile['EC']

        self.assertCountEqual(EC_profile.keys(), ['data_epistemology', 'epistemology_method',
                                                  'description', 'profile_data'])
        self.assertEqual(EC_profile['data_epistemology'], 'predicted')
        self.assertEqual(EC_profile['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(EC_profile['description'])
        self.assertCountEqual(data_ids,
                              EC_profile['profile_data']['col_ids'])

        self.assertCountEqual(community_profile.keys(), ['pathway', 'sample_set_ref'])
        self.assertEqual(community_profile['sample_set_ref'], '1/1/1')
        pathway_profile = community_profile['pathway']

        self.assertCountEqual(pathway_profile.keys(), ['data_epistemology', 'epistemology_method',
                                                       'description', 'profile_data'])
        self.assertEqual(pathway_profile['data_epistemology'], 'predicted')
        self.assertEqual(pathway_profile['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(pathway_profile['description'])
        self.assertCountEqual(data_ids,
                              pathway_profile['profile_data']['col_ids'])

        # import community profile and organism profile with custom profiles
        params = {'workspace_id': self.wsId,
                  'func_profile_obj_name': 'test_func_profile',
                  'original_matrix_ref': '1/1/1',
                  'community_profile': {'sample_set_ref': '1/1/1',
                                        'profiles': {'pathway': {'data_epistemology': 'predicted',
                                                                 'epistemology_method': 'FAPROTAX',
                                                                 'profile_file_path': profile_file_path},
                                                     'func_table': {'data_epistemology': 'predicted',
                                                                    'epistemology_method': 'FAPROTAX',
                                                                    'profile_file_path': profile_file_path}}},
                  'organism_profile': {'amplicon_set_ref': '1/1/1',
                                       'profiles': {'EC': {'data_epistemology': 'predicted',
                                                           'epistemology_method': 'FAPROTAX',
                                                           'profile_file_path': profile_file_path},
                                                    'groups': {'data_epistemology': 'predicted',
                                                               'epistemology_method': 'FAPROTAX',
                                                               'profile_file_path': profile_file_path}}}}
        func_profile_ref = self.serviceImpl.import_func_profile(self.ctx, params)[0]['func_profile_ref']

        func_profile_data_str = 'null'.join(func_profile_ref.split("None")[1:-1]).strip('/').replace("'", '"')
        func_profile_data = json.loads(func_profile_data_str)

        self.assertCountEqual(func_profile_data.keys(), ['original_matrix_ref',
                                                         'community_profile',
                                                         'organism_profile'])
        organism_profile = func_profile_data['organism_profile']
        community_profile = func_profile_data['community_profile']

        self.assertCountEqual(organism_profile.keys(), ['EC', 'amplicon_set_ref', 'custom_profiles'])
        self.assertEqual(organism_profile['amplicon_set_ref'], '1/1/1')
        EC_profile = organism_profile['EC']
        custom_profiles = organism_profile['custom_profiles']

        self.assertCountEqual(EC_profile.keys(), ['data_epistemology', 'epistemology_method',
                                                  'description', 'profile_data'])
        self.assertEqual(EC_profile['data_epistemology'], 'predicted')
        self.assertEqual(EC_profile['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(EC_profile['description'])
        self.assertCountEqual(data_ids,
                              EC_profile['profile_data']['col_ids'])

        self.assertCountEqual(custom_profiles.keys(), ['groups'])
        groups_profile = custom_profiles['groups']
        self.assertEqual(groups_profile['data_epistemology'], 'predicted')
        self.assertEqual(groups_profile['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(groups_profile['description'])
        self.assertCountEqual(data_ids,
                              groups_profile['profile_data']['col_ids'])

        self.assertCountEqual(community_profile.keys(), ['pathway', 'sample_set_ref', 'custom_profiles'])
        self.assertEqual(community_profile['sample_set_ref'], '1/1/1')
        pathway_profile = community_profile['pathway']
        custom_profiles = community_profile['custom_profiles']

        self.assertCountEqual(pathway_profile.keys(), ['data_epistemology', 'epistemology_method',
                                                       'description', 'profile_data'])
        self.assertEqual(pathway_profile['data_epistemology'], 'predicted')
        self.assertEqual(pathway_profile['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(pathway_profile['description'])
        self.assertCountEqual(data_ids,
                              pathway_profile['profile_data']['col_ids'])

        self.assertCountEqual(custom_profiles.keys(), ['func_table'])
        func_table_profile = custom_profiles['func_table']
        self.assertEqual(func_table_profile['data_epistemology'], 'predicted')
        self.assertEqual(func_table_profile['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(func_table_profile['description'])
        self.assertCountEqual(data_ids,
                              func_table_profile['profile_data']['col_ids'])

    @patch.object(SampleServiceUtil, "get_ids_from_samples", return_value=DATA_IDS)
    @patch.object(ProfileImporter, "_get_ids_from_amplicon_set", return_value=DATA_IDS)
    def test_import_func_profile_real_test(self, get_ids_from_samples, _get_ids_from_amplicon_set):

        data_ids = ['PB-Low-5', 'PB-High-5', 'PB-Low-6', 'PB-High-6',
                    'PB-Low-7', 'PB-High-7', 'PB-Low-8', 'PB-High-8']
        profile_file_path = os.path.join('data', 'func_table.tsv')
        fake_object_ref = self.createAnObject()

        params = {'workspace_id': self.wsId,
                  'func_profile_obj_name': 'test_func_profile',
                  'original_matrix_ref': fake_object_ref,
                  'community_profile': {'sample_set_ref': fake_object_ref,
                                        'profiles': {'pathway': {'data_epistemology': 'predicted',
                                                                 'epistemology_method': 'FAPROTAX',
                                                                 'profile_file_path': profile_file_path},
                                                     'func_table': {'data_epistemology': 'predicted',
                                                                    'epistemology_method': 'FAPROTAX',
                                                                    'profile_file_path': profile_file_path}}},
                  'organism_profile': {'amplicon_set_ref': fake_object_ref,
                                       'profiles': {'EC': {'data_epistemology': 'predicted',
                                                           'epistemology_method': 'FAPROTAX',
                                                           'profile_file_path': profile_file_path},
                                                    'groups': {'data_epistemology': 'predicted',
                                                               'epistemology_method': 'FAPROTAX',
                                                               'profile_file_path': profile_file_path}}}}
        func_profile_ref = self.serviceImpl.import_func_profile(self.ctx, params)[0]['func_profile_ref']

        func_profile_data = self.dfu.get_objects(
                                            {'object_refs': [func_profile_ref]})['data'][0]['data']

        self.assertCountEqual(func_profile_data.keys(), ['original_matrix_ref',
                                                         'community_profile',
                                                         'organism_profile'])
        organism_profile = func_profile_data['organism_profile']
        community_profile = func_profile_data['community_profile']

        self.assertCountEqual(organism_profile.keys(), ['EC', 'amplicon_set_ref', 'custom_profiles'])
        self.assertEqual(organism_profile['amplicon_set_ref'], fake_object_ref)
        EC_profile = organism_profile['EC']
        custom_profiles = organism_profile['custom_profiles']

        self.assertCountEqual(EC_profile.keys(), ['data_epistemology', 'epistemology_method',
                                                  'description', 'profile_data'])
        self.assertEqual(EC_profile['data_epistemology'], 'predicted')
        self.assertEqual(EC_profile['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(EC_profile['description'])
        self.assertCountEqual(data_ids,
                              EC_profile['profile_data']['col_ids'])

        self.assertCountEqual(custom_profiles.keys(), ['groups'])
        groups_profile = custom_profiles['groups']
        self.assertEqual(groups_profile['data_epistemology'], 'predicted')
        self.assertEqual(groups_profile['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(groups_profile['description'])
        self.assertCountEqual(data_ids,
                              groups_profile['profile_data']['col_ids'])

        self.assertCountEqual(community_profile.keys(), ['pathway', 'sample_set_ref', 'custom_profiles'])
        self.assertEqual(community_profile['sample_set_ref'], fake_object_ref)
        pathway_profile = community_profile['pathway']
        custom_profiles = community_profile['custom_profiles']

        self.assertCountEqual(pathway_profile.keys(), ['data_epistemology', 'epistemology_method',
                                                       'description', 'profile_data'])
        self.assertEqual(pathway_profile['data_epistemology'], 'predicted')
        self.assertEqual(pathway_profile['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(pathway_profile['description'])
        self.assertCountEqual(data_ids,
                              pathway_profile['profile_data']['col_ids'])

        self.assertCountEqual(custom_profiles.keys(), ['func_table'])
        func_table_profile = custom_profiles['func_table']
        self.assertEqual(func_table_profile['data_epistemology'], 'predicted')
        self.assertEqual(func_table_profile['epistemology_method'], 'FAPROTAX')
        self.assertIsNone(func_table_profile['description'])
        self.assertCountEqual(data_ids,
                              func_table_profile['profile_data']['col_ids'])
