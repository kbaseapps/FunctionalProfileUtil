
import errno
import logging
import os

from installed_clients.DataFileUtilClient import DataFileUtil


class ProfileImporter:

    @staticmethod
    def _mkdir_p(path):
        """
        _mkdir_p: make directory for given path
        """
        if not path:
            return
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    @staticmethod
    def _validate_params(params, expected, opt_param=set()):
        """Validates that required parameters are present. Warns if unexpected parameters appear"""
        expected = set(expected)
        opt_param = set(opt_param)
        pkeys = set(params)
        if expected - pkeys:
            raise ValueError("Required keys {} not in supplied parameters"
                             .format(", ".join(expected - pkeys)))
        defined_param = expected | opt_param
        for param in params:
            if param not in defined_param:
                logging.warning("Unexpected parameter {} supplied".format(param))

    def _gen_func_profile(self, original_matrix_ref, community_profile, organism_profile):
        func_profile_data = dict()

        func_profile_data['original_matrix_ref'] = original_matrix_ref

        if community_profile:
            pass

        if organism_profile:
            pass

        return func_profile_data

    def __init__(self, config):
        self.callback_url = config['SDK_CALLBACK_URL']
        self.scratch = config['scratch']
        self.token = config['KB_AUTH_TOKEN']
        self.dfu = DataFileUtil(self.callback_url)

        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)

    def import_func_profile(self, params):

        logging.info("start importing FunctionalProfile with params:{}".format(params))

        self._validate_params(params, ('workspace_id',
                                       'func_profile_obj_name',
                                       'original_matrix_ref'))

        workspace_id = params.get('workspace_id')
        func_profile_obj_name = params.get('func_profile_obj_name')

        original_matrix_ref = params.get('original_matrix_ref')
        community_profile = params.get('community_profile')
        organism_profile = params.get('organism_profile')

        func_profile_data = self._gen_func_profile(original_matrix_ref,
                                                   community_profile,
                                                   organism_profile)

        logging.info('start saving FunctionalProfile object: {}'.format(func_profile_obj_name))
        info = self.dfu.save_objects({
            "id": workspace_id,
            "objects": [{
                "type": "KBaseFunctionalProfile.FunctionalProfile",
                "data": func_profile_data,
                "name": func_profile_obj_name
            }]
        })[0]

        func_profile_ref = "%s/%s/%s" % (info[6], info[0], info[4])

        returnVal = {'func_profile_ref': func_profile_ref}

        return returnVal
