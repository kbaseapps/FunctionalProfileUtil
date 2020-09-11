/*
A KBase module: KBaseFunctionalProfile
*/

module KBaseFunctionalProfile {

    /* A boolean - 0 for false, 1 for true.
      @range (0, 1)
    */
    typedef int bool;

    /* Ref to a WS object
      @id ws
    */
    typedef string WSRef;

    /*
      A simple 2D matrix of values with labels/ids for rows and
      columns.  The matrix is stored as a list of lists, with the outer list
      containing rows, and the inner lists containing values for each column of
      that row.  Row/Col ids should be unique.

      row_ids - unique ids for rows.
      col_ids - unique ids for columns.
      values - two dimensional array indexed as: values[row][col]
               list<list<UnspecifiedObject>> values;
      @metadata ws length(row_ids) as n_rows
      @metadata ws length(col_ids) as n_cols
    */
    typedef structure {
      list<string> row_ids;
      list<string> col_ids;
      list<UnspecifiedObject> values;
    } Matrix2D;

    /*
      A structure that stores profiling data and metadata associated with profile

      data_epistemology - how was data acquired. one of: measured, asserted, predicted
      epistemology_method - method/program to be used to acquired data. e.g. FAPROTAX, PICRUSt2

      @optional description data_epistemology epistemology_method
    */
    typedef structure {
      string data_epistemology;
      string epistemology_method;
      string description;
      Matrix2D profile_data;
    } ProfileTable;

    /*
      A structure that stores multiple profile tables

      sample_set_ref - associated with community_profile
      amplicon_set_ref - associated with organism_profile

      @optional sample_set_ref amplicon_set_ref pathway EC KO custom_profiles
    */
    typedef structure {
      WSRef sample_set_ref;
      WSRef amplicon_set_ref;
      ProfileTable pathway;
      ProfileTable EC;
      ProfileTable KO;
      mapping<string, ProfileTable> custom_profiles;
    } Profile;

    /*
      A structure that captures an understanding of the functional capabilities of
      organisms and communities

      @optional original_matrix_ref community_profile organism_profile

      @metadata ws original_matrix_ref as original_matrix_ref
    */
    typedef structure {
      WSRef original_matrix_ref;
      Profile community_profile;
      Profile organism_profile;
    } FunctionalProfile;

};
