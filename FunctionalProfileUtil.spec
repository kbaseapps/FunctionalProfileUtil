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
      profile_file_path - either a local file path or staging file path
      staging_file - profile_file_path provided in ProfileTable is a staging file path. default: False
      build_report - build report for narrative. default: False
      profile_type - type of profile. e.g. amplicon, MG
      profile_category - category of profile. one of community or organism

      one of:
      sample_set_ref - associated with community_profile
      amplicon_set_ref - associated with organism_profile

      optional arguments:
      original_matrix_ref - original matrix object associated with this functional profile object
      data_epistemology - how was data acquired. one of: measured, asserted, predicted
      epistemology_method - method/program to be used to acquired data. e.g. FAPROTAX, PICRUSt2
      description - description for the profile
    */
    typedef structure {
      int workspace_id;
      string func_profile_obj_name;
      string profile_file_path;
      bool staging_file;
      bool build_report;

      WSRef original_matrix_ref;
      WSRef sample_set_ref;
      WSRef amplicon_set_ref;

      string data_epistemology;
      string epistemology_method;
      string description;
      string profile_type;
      string profile_category;

    } ImportFuncProfileParams;

    typedef structure {
      WSRef func_profile_ref;
      string report_name;
      WSRef report_ref;
    } ImportFuncProfileResults;

    funcdef import_func_profile(ImportFuncProfileParams params) returns (ImportFuncProfileResults returnVal) authentication required;

    typedef structure {

      WSRef func_profile_ref;
    } ReportResults;

    funcdef narrative_import_func_profile(mapping<string,UnspecifiedObject> params) returns (ReportResults returnVal) authentication required;

};
