/*
A KBase module: gottcha2
*/

module gottcha2 {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef run_gottcha2(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

};
