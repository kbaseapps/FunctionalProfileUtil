
import errno
import logging
import os
import pandas as pd
from xlrd.biffh import XLRDError

from installed_clients.DataFileUtilClient import DataFileUtil
from FunctionalProfileUtil.Utils.SampleServiceUtil import SampleServiceUtil

DATA_EPISTEMOLOGY = ['measured', 'asserted', 'predicted']


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

    @staticmethod
    def _file_to_df(file_path):
        logging.info('start parsing file content to data frame')

        try:
            df = pd.read_excel(file_path, sheet_name='data', index_col=0)

        except XLRDError:
            try:
                df = pd.read_excel(file_path, index_col=0)
                logging.warning('WARNING: A sheet named "data" was not found in the attached file,'
                                ' proceeding with the first sheet as the data sheet.')

            except XLRDError:

                try:
                    reader = pd.read_csv(file_path, sep=None, iterator=True)
                    inferred_sep = reader._engine.data.dialect.delimiter
                    df = pd.read_csv(file_path, sep=inferred_sep, index_col=0)
                except Exception:
                    err_msg = 'Cannot parse file. Please provide valide tsv, excel or csv file'
                    raise ValueError(err_msg)

        df.index = df.index.astype('str')
        df.columns = df.columns.astype('str')
        # fill NA with "None" so that they are properly represented as nulls in the KBase Object
        df = df.where((pd.notnull(df)), None)

        return df

    def _get_ids_from_amplicon_set(self, amplicon_set_ref):
        logging.info('start retrieving OTU ids from amplicon set')

        amplicon_set_data = self.dfu.get_objects(
                                            {'object_refs': [amplicon_set_ref]})['data'][0]['data']

        amplicons = amplicon_set_data.get('amplicons')

        return amplicons.keys()

    def _build_profile_table(self, profile_file_path, staging_file, data_ids):

        if not profile_file_path:
            raise ValueError('Missing profile file path')

        logging.info('start reading {}'.format(os.path.basename(profile_file_path)))
        if staging_file:
            logging.info('start downloading staging file')
            download_staging_file_params = {'staging_file_subdir_path': profile_file_path}
            profile_file_path = self.dfu.download_staging_file(
                                                download_staging_file_params).get('copy_file_path')

        df = self._file_to_df(profile_file_path)

        # check profile file has all item ids from sample/amplicon set object
        unmatched_ids = set(data_ids) - set(df.columns)
        if unmatched_ids:
            msg = 'Found some unmatched set data ids in profile file columns\n{}'.format(
                                                                                    unmatched_ids)
            logging.warning(msg)
            df = df.T
            unmatched_ids = set(data_ids) - set(df.columns)
            if unmatched_ids:
                msg = 'Found some unmatched set data ids in profile file rows\n{}'.format(
                                                                                    unmatched_ids)
                logging.warning(msg)
                err_msg = 'Profile file does not contain all data ids from sample or amplicon set'
                raise ValueError(err_msg)

        profile_data = {'row_ids': df.index.tolist(),
                        'col_ids': df.columns.tolist(),
                        'values': df.values.tolist()}

        return profile_data

    def _build_profile_data(self, data_ids, profiles, staging_file):
        logging.info('start building profile data')

        gen_profile_data = dict()
        for profile_name, profile_table in profiles.items():

            data_epistemology = profile_table.get('data_epistemology')

            if data_epistemology:
                data_epistemology = data_epistemology.lower()
                if data_epistemology not in DATA_EPISTEMOLOGY:
                    err_msg = 'Data epistemology can only be one of {}'.format(DATA_EPISTEMOLOGY)
                    raise ValueError(err_msg)

            epistemology_method = profile_table.get('epistemology_method')
            description = profile_table.get('description')
            profile_file_path = profile_table.get('profile_file_path')

            logging.info('start building profile table for {}'.format(profile_name))
            profile_data = self._build_profile_table(profile_file_path, staging_file, data_ids)

            if profile_name in ['pathway', 'EC', 'KO']:
                gen_profile_data[profile_name] = {'data_epistemology': data_epistemology,
                                                  'epistemology_method': epistemology_method,
                                                  'description': description,
                                                  'profile_data': profile_data}
            else:
                if not gen_profile_data.get('custom_profiles'):
                    gen_profile_data['custom_profiles'] = dict()
                gen_profile_data['custom_profiles'][profile_name] = {
                                                        'data_epistemology': data_epistemology,
                                                        'epistemology_method': epistemology_method,
                                                        'description': description,
                                                        'profile_data': profile_data}

        return gen_profile_data

    def _gen_func_profile(self, original_matrix_ref, community_profile, organism_profile,
                          staging_file):
        func_profile_data = dict()

        func_profile_data['original_matrix_ref'] = original_matrix_ref

        if community_profile:
            logging.info('start building community profile')
            sample_set_ref = community_profile.get('sample_set_ref')
            if not sample_set_ref:
                raise ValueError('Missing sample_set_ref in community profile')
            data_ids = self.sampleservice_util.get_ids_from_samples(sample_set_ref)

            comm_profile = self._build_profile_data(data_ids,
                                                    community_profile.get('profiles'),
                                                    staging_file)
            comm_profile['sample_set_ref'] = sample_set_ref

            func_profile_data['community_profile'] = comm_profile

        if organism_profile:
            logging.info('start building organism profile')
            amplicon_set_ref = organism_profile.get('amplicon_set_ref')
            if not amplicon_set_ref:
                raise ValueError('Missing amplicon_set_ref in organism profile')

            data_ids = self._get_ids_from_amplicon_set(amplicon_set_ref)

            org_profile = self._build_profile_data(data_ids,
                                                   organism_profile.get('profiles'),
                                                   staging_file)

            org_profile['amplicon_set_ref'] = amplicon_set_ref

            func_profile_data['organism_profile'] = org_profile

        return func_profile_data

    def __init__(self, config):
        self.callback_url = config['SDK_CALLBACK_URL']
        self.scratch = config['scratch']
        self.token = config['KB_AUTH_TOKEN']
        self.dfu = DataFileUtil(self.callback_url)
        self.sampleservice_util = SampleServiceUtil(config)

        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)

    def import_func_profile(self, params):

        logging.info("start importing FunctionalProfile with params:{}".format(params))

        self._validate_params(params, ('workspace_id',
                                       'func_profile_obj_name',
                                       'original_matrix_ref'))

        workspace_id = params.get('workspace_id')
        func_profile_obj_name = params.get('func_profile_obj_name')
        staging_file = params.get('staging_file', False)

        original_matrix_ref = params.get('original_matrix_ref')
        community_profile = params.get('community_profile')
        organism_profile = params.get('organism_profile')

        func_profile_data = self._gen_func_profile(original_matrix_ref,
                                                   community_profile,
                                                   organism_profile,
                                                   staging_file)

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
