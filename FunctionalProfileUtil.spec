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

    typedef string profile_name;

    /*
      profile_file_path - either a local file path or staging file path
      optional arguments:
      data_epistemology - how was data acquired. one of: measured, asserted, predicted
      epistemology_method - method/program to be used to acquired data. e.g. FAPROTAX, PICRUSt2
      description - description for the profile
    */
    typedef structure {
      string data_epistemology;
      string epistemology_method;
      string description;
      string profile_file_path;
    } ProfileTable;

    /*
      community based functional profile
      sample_set_ref - sample set associated with profile.
    */
    typedef structure {
      WSRef sample_set_ref;
      mapping<profile_name, ProfileTable> profiles;
    } CommProfile;

    /*
      organism based functional profile
      amplicon_set_ref - amplicon set associated with profile.
    */
    typedef structure {
      WSRef amplicon_set_ref;
      mapping<profile_name, ProfileTable> profiles;
    } OrgProfile;

    /*
      staging_file - profile_file_path provided in ProfileTable is a staging file path. default: False
    */
    typedef structure {
      int workspace_id;
      string func_profile_obj_name;
      bool staging_file;

      WSRef original_matrix_ref;
      CommProfile community_profile;
      OrgProfile organism_profile;
    } ImportFuncProfileParams;

    typedef structure {
      WSRef func_profile_ref;
    } ImportFuncProfileResults;

    funcdef import_func_profile(ImportFuncProfileParams params) returns (ImportFuncProfileResults returnVal) authentication required;

    typedef structure {
      string report_name;
      WSRef report_ref;
      WSRef func_profile_ref;
    } ReportResults;

    funcdef narrative_import_func_profile(mapping<string,UnspecifiedObject> params) returns (ReportResults returnVal) authentication required;

};
