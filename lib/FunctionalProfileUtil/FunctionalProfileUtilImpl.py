# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os

from installed_clients.KBaseReportClient import KBaseReport
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
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/Tianhao-Gu/FunctionalProfileUtil.git"
    GIT_COMMIT_HASH = "9d6b351995f9fe5bd186fa3c59d5deef3d3ac1b1"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def import_func_profile(self, ctx, params):
        """
        :param params: instance of type "ImportFuncProfileParams" ->
           structure: parameter "original_matrix_ref" of type "WSRef" (Ref to
           a WS object @id ws), parameter "community_profile" of type
           "CommProfile" -> structure: parameter "sample_set_ref" of type
           "WSRef" (Ref to a WS object @id ws), parameter "profiles" of
           mapping from type "profile_name" to type "ProfileTable" ->
           structure: parameter "data_epistemology" of String, parameter
           "epistemology_method" of String, parameter "description" of
           String, parameter "profile_file_path" of String, parameter
           "organism_profile" of type "OrgProfile" -> structure: parameter
           "amplicon_set_ref" of type "WSRef" (Ref to a WS object @id ws),
           parameter "profiles" of mapping from type "profile_name" to type
           "ProfileTable" -> structure: parameter "data_epistemology" of
           String, parameter "epistemology_method" of String, parameter
           "description" of String, parameter "profile_file_path" of String
        :returns: instance of type "ImportFuncProfileResults" -> structure:
           parameter "func_profile_ref" of type "WSRef" (Ref to a WS object
           @id ws)
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN import_func_profile
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
