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

    typedef structure {
      string data_epistemology;
      string epistemology_method;
      string description;
      string profile_file_path;
    } ProfileTable;

    typedef structure {
      WSRef sample_set_ref;
      mapping<profile_name, ProfileTable> profiles;
    } CommProfile;

    typedef structure {
      WSRef amplicon_set_ref;
      mapping<profile_name, ProfileTable> profiles;
    } OrgProfile;

    typedef structure {
        int workspace_id;
        string func_profile_obj_name;

        WSRef original_matrix_ref;
        CommProfile community_profile;
        OrgProfile organism_profile;
    } ImportFuncProfileParams;

    typedef structure {
        WSRef func_profile_ref;
    } ImportFuncProfileResults;

    funcdef import_func_profile(ImportFuncProfileParams params) returns (ImportFuncProfileResults returnVal) authentication required;

};
