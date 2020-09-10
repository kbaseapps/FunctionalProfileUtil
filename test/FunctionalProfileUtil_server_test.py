# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser

from FunctionalProfileUtil.FunctionalProfileUtilImpl import FunctionalProfileUtil
from FunctionalProfileUtil.Utils.ProfileImporter import ProfileImporter
from FunctionalProfileUtil.FunctionalProfileUtilServer import MethodContext
from FunctionalProfileUtil.authclient import KBaseAuth as _KBaseAuth

from installed_clients.WorkspaceClient import Workspace


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

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def test_import_func_profile_fail(self):
        with self.assertRaisesRegex(ValueError, "Required keys"):
            self.serviceImpl.import_func_profile(self.ctx, {})

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
