# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import sys
import subprocess
import shutil
from installed_clients.WorkspaceClient import Workspace as workspaceService
import requests
from pprint import pprint, pformat
from datetime import datetime
import re

from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.ReadsUtilsClient import ReadsUtils
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.SetAPIServiceClient import SetAPI
#END_HEADER


class gottcha2:
    '''
    Module Name:
    gottcha2

    Module Description:
    A KBase module: gottcha2
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.6"
    GIT_URL = "git@github.com:LANL-Bioinformatics/kbase-gottcha2.git"
    GIT_COMMIT_HASH = "1a607a2de1ecf577ee0a98ce15660a5baa2ab429"

    #BEGIN_CLASS_HEADER
    def _generate_DataTable(self, infile, outfile):
        f =  open(infile, "r")
        wf = open(outfile,"w")

        header = f.readline().strip()
        headerlist = [ x.strip() for x in header.split('\t')]

        wf.write("<head>\n")
        wf.write("<link rel='stylesheet' type='text/css' href='https://cdn.datatables.net/1.10.19/css/jquery.dataTables.css'>\n")
        wf.write("<script type='text/javascript' charset='utf8' src='https://code.jquery.com/jquery-3.3.1.js'></script>\n")
        wf.write("<script type='text/javascript' charset='utf8' src='https://cdn.datatables.net/1.10.19/js/jquery.dataTables.min.js'></script>\n")
        wf.write("</head>\n")
        wf.write("<body>\n")
        wf.write("""<script>
        $(document).ready(function() {
            $('#gottcha2_result_table').DataTable();
        } );
        </script>""")
        wf.write("<table id='gottcha2_result_table' class='display' style=''>\n")
        wf.write('<thead><tr>' + ''.join("<th>{0}</th>".format(t) for t in headerlist) + '</tr></thead>\n')
        wf.write("<tbody>\n")
        for line in f:
            if not line.strip():continue 
            wf.write("<tr>\n")
            temp = [ x.strip() for x in line.split('\t')]
            wf.write(''.join("<td>{0}</td>".format(t) for t in temp))
            wf.write("</tr>\n")
        wf.write("</tbody>\n")
        wf.write("</table>")
        wf.write("</body>\n")

    def package_folder(self, folder_path, zip_file_name, zip_file_description):
        ''' Simple utility for packaging a folder and saving to shock '''
        if folder_path == self.scratch:
            raise ValueError ("cannot package scatch itself.  folder path: "+folder_path)
        elif not folder_path.startswith(self.scratch):
            raise ValueError ("cannot package folder that is not a subfolder of scratch.  folder path: "+folder_path)
        dfu = DataFileUtil(self.callback_url)
        if not os.path.exists(folder_path):
            raise ValueError ("cannot package folder that doesn't exist: "+folder_path)
        output = dfu.file_to_shock({'file_path': folder_path,
                                    'make_handle': 0,
                                    'pack': 'zip'})
        return {'shock_id': output['shock_id'],
                'name': zip_file_name,
                'label': zip_file_description}

    def log(self, target, message):
        if target is not None:
            target.append(message)
        print(message)
        sys.stdout.flush()


    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.scratch = config['scratch']
        self.workspaceURL = config['workspace-url']
        self.shockURL = config['shock-url']
        self.handleURL = config['handle-service-url']
        self.serviceWizardURL = config['service-wizard-url']
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)

        if not os.path.exists(self.scratch):
            os.makedirs(self.scratch)
        os.chdir(self.scratch)

        #END_CONSTRUCTOR
        pass


    def run_gottcha2(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_gottcha2

        # Step 2 - Download the input data as a FASTQ and
        # We can use the ReadsUtils module to download a FASTQ file from our Reads data object.
        # The return object gives us the path to the file that was created.
        logging.info('Downloading Reads data as a Fastq file.')
        logging.info(f'params {params}')
        token = ctx['token']
        wsClient = workspaceService(self.workspaceURL, token=token)
        env = os.environ.copy()
        env['KB_AUTH_TOKEN'] = token

        # object info
        [OBJID_I, NAME_I, TYPE_I, SAVE_DATE_I, VERSION_I, SAVED_BY_I, WSID_I, WORKSPACE_I, CHSUM_I, SIZE_I,
         META_I] = range(11)  # object_info tuple

        Set_types = ["KBaseSets.ReadsSet", "KBaseRNASeq.RNASeqSampleSet"]
        PE_types = ["KBaseFile.PairedEndLibrary", "KBaseAssembly.PairedEndLibrary"]
        SE_types = ["KBaseFile.SingleEndLibrary", "KBaseAssembly.SingleEndLibrary"]
        acceptable_types = Set_types + PE_types + SE_types

        # Determine whether read library or read set is input object
        #
        try:
            input_reads_obj_info = wsClient.get_object_info([{'ref': params['input_refs'][0]}], 1)[0]
            input_reads_obj_type = input_reads_obj_info[TYPE_I]
            input_reads_obj_type = re.sub('-[0-9]+\.[0-9]+$', "", input_reads_obj_type)  # remove trailing version
            # input_reads_obj_version = input_reads_obj_info[VERSION_I]  # this is object version, not type version
        except Exception as e:
            raise ValueError('Unable to get read library object from workspace: (' + str(
                params['input_refs']) + ')' + str(e))

        if input_reads_obj_type not in acceptable_types:
            raise ValueError(
                "Input reads of type: '" + input_reads_obj_type + "'.  Must be one of " + ", ".join(acceptable_types))

        # auto-detect reads type
        read_type = None
        if input_reads_obj_type in PE_types:
            read_type = 'PE'
        elif input_reads_obj_type in SE_types:
            read_type = 'SE'

        # get set
        #
        readsSet_ref_list = []
        readsSet_names_list = []
        if input_reads_obj_type in Set_types:
            try:
                # self.log (console, "INPUT_READS_REF: '"+input_params['input_refs']+"'")  # DEBUG
                # setAPI_Client = SetAPI (url=self.callbackURL, token=ctx['token'])  # for SDK local.  doesn't work for SetAPI
                setAPI_Client = SetAPI(url=self.serviceWizardURL, token=ctx['token'],
                                       service_ver='beta')  # for dynamic service
                input_readsSet_obj = setAPI_Client.get_reads_set_v1(
                    {'ref': params['input_refs'][0], 'include_item_info': 1})

            except Exception as e:
                raise ValueError('SetAPI FAILURE: Unable to get read library set object from workspace: (' + str(
                    params['input_refs']) + ")\n" + str(e))
            logging.info(f"reads set items {input_readsSet_obj['data']['items']}")
            for readsLibrary_obj in input_readsSet_obj['data']['items']:
                readsSet_ref_list.append(readsLibrary_obj['ref'])
                readsSet_names_list.append(readsLibrary_obj['info'][NAME_I])
                reads_item_type = readsLibrary_obj['info'][TYPE_I]
                reads_item_type = re.sub('-[0-9]+\.[0-9]+$', "", reads_item_type)  # remove trailing version
                if reads_item_type in PE_types:
                    this_read_type = 'PE'
                elif reads_item_type in SE_types:
                    this_read_type = 'SE'
                else:
                    raise ValueError(
                        "Can't handle read item type '" + reads_item_type + "' obj_name: '" + readsLibrary_obj['info'][
                            NAME_I] + " in Set: '" + str(params['input_refs']) + "'")
                if read_type != None and this_read_type != read_type:
                    raise ValueError("Can't handle read Set: '" + str(params[
                                                                          'input_refs']) + "'.  Unable to process mixed PairedEndLibrary and SingleEndLibrary.  Please split into separate ReadSets")
                elif read_type == None:
                    read_type = this_read_type
        else:
            readsSet_ref_list = params['input_refs']
            readsSet_names_list = input_reads_obj_info[NAME_I]

        for reads_item_i,input_reads_library_ref in enumerate(readsSet_ref_list):
            params['input_ref'] = input_reads_library_ref
            params['read_type']= read_type

            output = self.exec_gottcha2(ctx, params)[0]

        #END run_gottcha2

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_gottcha2 return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def exec_gottcha2(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN exec_gottcha2
        console = []
        self.log(console, 'Running GOTTCHA2 with parameters: ')
        self.log(console, "\n" + pformat(params))
        report = ''
        retVal = dict()
        token = ctx['token']
        wsClient = workspaceService(self.workspaceURL, token=token)
        headers = {'Authorization': 'OAuth ' + token}
        env = os.environ.copy()
        env['KB_AUTH_TOKEN'] = token
        # object info
        [OBJID_I, NAME_I, TYPE_I, SAVE_DATE_I, VERSION_I, SAVED_BY_I, WSID_I, WORKSPACE_I, CHSUM_I, SIZE_I,
         META_I] = range(11)  # object_info tuple

        # Set_types = ["KBaseSets.ReadsSet", "KBaseRNASeq.RNASeqSampleSet"]
        PE_types = ["KBaseFile.PairedEndLibrary", "KBaseAssembly.PairedEndLibrary"]
        SE_types = ["KBaseFile.SingleEndLibrary", "KBaseAssembly.SingleEndLibrary"]
        acceptable_types = PE_types + SE_types
        # Determine whether read library is of correct type
        #
        try:
            input_reads_obj_info = \
                wsClient.get_object_info_new({'objects': [{'ref': params['input_ref']}]})[0]
            input_reads_obj_type = input_reads_obj_info[TYPE_I]
            # input_reads_obj_version = input_reads_obj_info[VERSION_I]  # this is object version, not type version

        except Exception as e:
            raise ValueError('Unable to get read library object from workspace: (' + str(
                params['input_ref']) + ')' + str(e))

        input_reads_obj_type = re.sub('-[0-9]+\.[0-9]+$', "", input_reads_obj_type)  # remove trailing version
        acceptable_types = PE_types + SE_types
        if input_reads_obj_type not in acceptable_types:
            raise ValueError(
                "Input reads of type: '" + input_reads_obj_type + "'.  Must be one of " + ", ".join(acceptable_types))

        # Ensure that all libraries in ReadsSet are either single-ended or pair ended
        #
        if params['read_type'] == 'PE' and not input_reads_obj_type in PE_types:
            raise ValueError("read_type set to 'Paired End' but object is SingleEndLibrary")
        if params['read_type'] == 'SE' and not input_reads_obj_type in SE_types:
            raise ValueError("read_type set to 'Single End' but object is PairedEndLibrary")

        # Instatiate ReadsUtils
        #
        try:
            readsUtils_Client = ReadsUtils(url=self.callback_url, token=ctx['token'])  # SDK local

            download_reads_output = readsUtils_Client.download_reads({'read_libraries': [params['input_ref']],
                                                                      'interleaved': 'false'
                                                                      })
        except Exception as e:
            raise ValueError('Unable to get read library object from workspace: (' + str(
                params['input_ref']) + ")\n" + str(e))

        logging.info(
            f"Input parameters {params['input_refs']}, {params['db_type']} download_reads_output {download_reads_output}")
        fastq_files = []
        fastq_files_name = []
        for key, val in download_reads_output['files'].items():
            if 'fwd' in val['files'] and val['files']['fwd']:
                fastq_files.append(val['files']['fwd'])
                fastq_files_name.append(val['files']['fwd_name'])
            if 'rev' in val['files'] and val['files']['rev']:
                fastq_files.append(val['files']['rev'])
                fastq_files_name.append(val['files']['rev_name'])
        logging.info(f"fastq files {fastq_files}")
        fastq_files_string = ' '.join(fastq_files)
        output_dir = os.path.join(self.scratch, 'gottcha2_output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        ## default options
        if 'min_coverage' not in params:
            params['min_coverage'] = 0.005
        if 'min_reads' not in params:
            params['min_reads'] = 3
        if 'min_length' not in params:
            params['min_length'] = 60
        if 'max_zscore' not in params:
            params['max_zscore'] = 10
        outprefix = "gottcha2"

        cmd = ['/kb/module/lib/gottcha2/src/uge-gottcha2.sh', '-i', fastq_files_string, '-t', '4', '-o', output_dir,
               '-p',
               outprefix, '-d', '/data/gottcha2/RefSeq90/' + params['db_type'], '-c', str(params['min_coverage']), '-r',
               str(params['min_reads']), '-s', str(params['min_length']), '-z', str(params['max_zscore'])]
        logging.info(f'cmd {cmd}')
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logging.info(f'subprocess {p.communicate()}')
        summary_file = os.path.join(output_dir, outprefix + '.summary.tsv')
        lineage_file = os.path.join(output_dir, outprefix + '.lineage.tsv')

        if os.stat(lineage_file).st_size == 0:
            msg = 'There is no taxonomy classification assignment against ' + params[
                'db_type'] + ' reference DB. You may try another reference DB.'
            logging.error(msg)
            raise ValueError(msg)

        # generate report directory and html file
        report_dir = os.path.join(output_dir, 'html_report')
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        summary_file_dt = os.path.join(report_dir, 'gottcha2.datatable.html')

        self._generate_DataTable(summary_file, summary_file_dt)
        shutil.copy2('/kb/module/lib/gottcha2/src/index.html', os.path.join(report_dir, 'index.html'))
        shutil.copy2(os.path.join(output_dir, outprefix + '.krona.html'),
                     os.path.join(report_dir, 'gottcha2.krona.html'))
        if os.path.exists(os.path.join(output_dir, outprefix + '.tree.svg')):
            shutil.move(os.path.join(output_dir, outprefix + '.tree.svg'),
                        os.path.join(report_dir, 'gottcha2.tree.svg'))
        html_zipped = self.package_folder(report_dir, 'index.html', 'index.html')

        # Step 5 - Build a Report and return
        objects_created = []
        output_files = os.listdir(output_dir)
        output_files_list = []
        for output in output_files:
            if not os.path.isdir(output):
                output_files_list.append({'path': os.path.join(output_dir, output),
                                          'name': output
                                          })
        # not used
        output_html_files = [{'path': os.path.join(report_dir, 'index.html'),
                              'name': 'index.html'},
                             {'path': os.path.join(report_dir, 'gottcha2.krona.html'),
                              'name': 'gottcha2.krona.html'},
                             {'path': os.path.join(report_dir, 'gottcha2.datatable.html'),
                              'name': 'gottcha2.datatable.html'},
                             {'path': os.path.join(report_dir, 'gottcha2.tree.svg'),
                              'name': 'gottcha2.tree.svg'}
                             ]
        message = 'GOTTCHA2 run finished on %s against %s.' % (','.join(fastq_files_name), params['db_type'])
        report_params = {'message': message,
                         'workspace_name': params.get('workspace_name'),
                         'objects_created': objects_created,
                         'file_links': output_files_list,
                         'html_links': [html_zipped],
                         'direct_html_link_index': 0,
                         'html_window_height': 460}

        # STEP 6: contruct the output to send back
        kbase_report_client = KBaseReport(self.callback_url)
        report_output = kbase_report_client.create_extended_report(report_params)
        report_output['report_params'] = report_params
        logging.info(f'report output {report_output}')

        # Return references which will allow inline display of
        # the report in the Narrative
        output = {'report_name': report_output['name'],
                  'report_ref': report_output['ref'],
                  'report_params': report_output['report_params']}

        #END exec_gottcha2

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method exec_gottcha2 return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
