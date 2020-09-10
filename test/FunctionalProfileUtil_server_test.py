# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser

from FunctionalProfileUtil.FunctionalProfileUtilImpl import FunctionalProfileUtil
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

        print('fdasfdsa')
        print(ret)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def test_import_func_profile_fail(self):
        with self.assertRaisesRegex(ValueError, "Required keys"):
            self.serviceImpl.import_func_profile(self.ctx, {})

    # def test_import_func_profile(self):
    #     ret = self.serviceImpl.import_func_profile(self.ctx, {'workspace_name': self.wsName,
    #                                                          'parameter_1': 'Hello World!'})
