/*
A KBase module: FunctionalProfileUtil
*/

module FunctionalProfileUtil {

    /* A boolean - 0 for false, 1 for true.
      @range (0, 1)
    */
    typedef int bool;

    /* Ref to a WS object
      @id ws
    */
    typedef string WSRef;

    /*
      func_profile_obj_name - result FunctionalProfile object name
      original_matrix_ref - original matrix object associated with this functional profile object
                            original matrix must have sample_set_ref for community_profile
                                                  and amplicon_set_ref for organism_profile
      profile_file_path - either a local file path or staging file path
      profile_type - type of profile. e.g. amplicon, MG
      profile_category - category of profile. one of community or organism

      optional arguments:
      staging_file - profile_file_path provided in ProfileTable is a staging file path. default: False
      build_report - build report for narrative. default: False
      data_epistemology - how was data acquired. one of: measured, asserted, predicted
      epistemology_method - method/program to be used to acquired data. e.g. FAPROTAX, PICRUSt2
      description - description for the profile
    */
    typedef structure {
      int workspace_id;
      string func_profile_obj_name;
      WSRef original_matrix_ref;
      string profile_file_path;
      string profile_type;
      string profile_category;

      bool staging_file;
      bool build_report;
      string data_epistemology;
      string epistemology_method;
      string description;
    } ImportFuncProfileParams;

    typedef structure {
      WSRef func_profile_ref;
      string report_name;
      WSRef report_ref;
    } ImportFuncProfileResults;

    funcdef import_func_profile(ImportFuncProfileParams params) returns (ImportFuncProfileResults returnVal) authentication required;

};
