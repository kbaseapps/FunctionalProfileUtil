# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os

from FunctionalProfileUtil.Utils.ProfileImporter import ProfileImporter
#END_HEADER


class FunctionalProfileUtil:
    '''
    Module Name:
    FunctionalProfileUtil

    Module Description:
    A KBase module: FunctionalProfileUtil
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "1.0.0"
    GIT_URL = "https://github.com/Tianhao-Gu/FunctionalProfileUtil.git"
    GIT_COMMIT_HASH = "9e7e450c14d286f791b5ff541734806f70132f89"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.config = config
        self.config['SDK_CALLBACK_URL'] = os.environ['SDK_CALLBACK_URL']
        self.config['KB_AUTH_TOKEN'] = os.environ['KB_AUTH_TOKEN']
        self.scratch = config['scratch']

        self.profile_importer = ProfileImporter(self.config)
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def import_func_profile(self, ctx, params):
        """
        :param params: instance of type "ImportFuncProfileParams"
           (profile_file_path - either a local file path or staging file path
           staging_file - profile_file_path provided in ProfileTable is a
           staging file path. default: False build_report - build report for
           narrative. default: False profile_type - type of profile. e.g.
           amplicon, MG profile_category - category of profile. one of
           community or organism one of: sample_set_ref - associated with
           community_profile amplicon_set_ref - associated with
           organism_profile optional arguments: original_matrix_ref -
           original matrix object associated with this functional profile
           object data_epistemology - how was data acquired. one of:
           measured, asserted, predicted epistemology_method - method/program
           to be used to acquired data. e.g. FAPROTAX, PICRUSt2 description -
           description for the profile) -> structure: parameter
           "workspace_id" of Long, parameter "func_profile_obj_name" of
           String, parameter "profile_file_path" of String, parameter
           "staging_file" of type "bool" (A boolean - 0 for false, 1 for
           true. @range (0, 1)), parameter "build_report" of type "bool" (A
           boolean - 0 for false, 1 for true. @range (0, 1)), parameter
           "original_matrix_ref" of type "WSRef" (Ref to a WS object @id ws),
           parameter "sample_set_ref" of type "WSRef" (Ref to a WS object @id
           ws), parameter "amplicon_set_ref" of type "WSRef" (Ref to a WS
           object @id ws), parameter "data_epistemology" of String, parameter
           "epistemology_method" of String, parameter "description" of
           String, parameter "profile_type" of String, parameter
           "profile_category" of String
        :returns: instance of type "ImportFuncProfileResults" -> structure:
           parameter "func_profile_ref" of type "WSRef" (Ref to a WS object
           @id ws), parameter "report_name" of String, parameter "report_ref"
           of type "WSRef" (Ref to a WS object @id ws)
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN import_func_profile
        returnVal = self.profile_importer.import_func_profile(params)
        #END import_func_profile

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method import_func_profile return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
