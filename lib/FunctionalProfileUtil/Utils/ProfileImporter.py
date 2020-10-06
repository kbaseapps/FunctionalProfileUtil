
import errno
import logging
import os
import pandas as pd
from xlrd.biffh import XLRDError
import uuid
import shutil

from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.kb_GenericsReportClient import kb_GenericsReport

from FunctionalProfileUtil.Utils.SampleServiceUtil import SampleServiceUtil

DATA_EPISTEMOLOGY = ['measured', 'asserted', 'predicted']
PROFILE_CATEGORY = ['community',  'organism']
PROFILE_TYPE = ['amplicon', 'mg']


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

        # df = df.applymap(str)

        return df

    def _save_func_profile(self, workspace_id, func_profile_data, func_profile_obj_name):
        logging.info('start saving FunctionalProfile object: {}'.format(func_profile_obj_name))
        info = self.dfu.save_objects({
            "id": workspace_id,
            "objects": [{
                "type": "KBaseProfile.FunctionalProfile",
                "data": func_profile_data,
                "name": func_profile_obj_name
            }]
        })[0]

        return "%s/%s/%s" % (info[6], info[0], info[4])

    def _generate_visualization_content(self, func_profile_ref, output_directory):
        func_profile_data = self.dfu.get_objects(
                                            {'object_refs': [func_profile_ref]})['data'][0]['data']

        data = func_profile_data.get('data')
        data_df = pd.DataFrame(data['values'],
                               index=data['row_ids'], columns=data['col_ids'])

        data_df.fillna(0, inplace=True)
        tsv_file_path = os.path.join(output_directory, 'heatmap_data_{}.tsv'.format(
                                                                    str(uuid.uuid4())))
        data_df.to_csv(tsv_file_path)
        heatmap_dir = self.report_util.build_heatmap_html({
                                            'tsv_file_path': tsv_file_path,
                                            'cluster_data': True})['html_dir']

        row_data_summary = data_df.T.describe().to_string()
        col_data_summary = data_df.describe().to_string()

        tab_def_content = ''
        tab_content = ''

        # build data summary page
        viewer_name = 'data_summary'
        tab_def_content += '''\n<div class="tab">\n'''
        tab_def_content += '''\n<button class="tablinks" '''
        tab_def_content += '''onclick="openTab(event, '{}')"'''.format(viewer_name)
        tab_def_content += ''' id="defaultOpen"'''
        tab_def_content += '''>Profile Aggregating Statistic</button>\n'''

        tab_content += '''\n<div id="{}" class="tabcontent" style="overflow:auto">'''.format(viewer_name)
        tab_content += '''\n<h5>Profile Size: {} x {}</h5>'''.format(len(data_df.index),
                                                                     len(data_df.columns))
        tab_content += '''\n<h5>Row Aggregating Statistic</h5>'''
        html = '''\n<pre class="tab">''' + str(row_data_summary).replace("\n", "<br>") + "</pre>"
        tab_content += html
        tab_content += '''\n<br>'''
        tab_content += '''\n<hr style="height:2px;border-width:0;color:gray;background-color:gray">'''
        tab_content += '''\n<br>'''
        tab_content += '''\n<h5>Column Aggregating Statistic</h5>'''
        html = '''\n<pre class="tab">''' + str(col_data_summary).replace("\n", "<br>") + "</pre>"
        tab_content += html
        tab_content += '\n</div>\n'

        # build profile heatmap page
        viewer_name = 'ProfileHeatmapViewer'
        tab_def_content += '''\n<button class="tablinks" '''
        tab_def_content += '''onclick="openTab(event, '{}')"'''.format(viewer_name)
        tab_def_content += '''>Profile Heatmap</button>\n'''

        heatmap_report_files = os.listdir(heatmap_dir)

        heatmap_index_page = None
        for heatmap_report_file in heatmap_report_files:
            if heatmap_report_file.endswith('.html'):
                heatmap_index_page = heatmap_report_file

            shutil.copy2(os.path.join(heatmap_dir, heatmap_report_file),
                         output_directory)

        if heatmap_index_page:
            tab_content += '''\n<div id="{}" class="tabcontent">'''.format(viewer_name)
            tab_content += '\n<iframe height="900px" width="100%" '
            tab_content += 'src="{}" '.format(heatmap_index_page)
            tab_content += 'style="border:none;"></iframe>'
            tab_content += '\n</div>\n'
        else:
            tab_content += '''\n<div id="{}" class="tabcontent">'''.format(viewer_name)
            tab_content += '''\n<p style="color:red;" >'''
            tab_content += '''Heatmap is too large to be displayed.</p>\n'''
            tab_content += '\n</div>\n'

        tab_def_content += '\n</div>\n'
        return tab_def_content + tab_content

    def _generate_html_report(self, func_profile_ref):

        logging.info('Start generating report page')

        output_directory = os.path.join(self.scratch, str(uuid.uuid4()))
        logging.info('Start generating html report in {}'.format(output_directory))

        html_report = list()

        self._mkdir_p(output_directory)
        result_file_path = os.path.join(output_directory, 'func_profile_viewer_report.html')

        visualization_content = self._generate_visualization_content(func_profile_ref,
                                                                     output_directory)

        with open(result_file_path, 'w') as result_file:
            with open(os.path.join(os.path.dirname(__file__),
                                   'templates', 'func_profile_template.html'),
                      'r') as report_template_file:
                report_template = report_template_file.read()
                report_template = report_template.replace('<p>Visualization_Content</p>',
                                                          visualization_content)
                result_file.write(report_template)

        report_shock_id = self.dfu.file_to_shock({'file_path': output_directory,
                                                  'pack': 'zip'})['shock_id']

        html_report.append({'shock_id': report_shock_id,
                            'name': os.path.basename(result_file_path),
                            'label': os.path.basename(result_file_path),
                            'description': 'HTML summary report for Import Amplicon Matrix App'
                            })
        return html_report

    def _gen_func_profile_report(self, func_profile_ref, workspace_id):
        logging.info('start generating report')

        objects_created = [{'ref': func_profile_ref, 'description': 'Imported FunctionalProfile'}]

        output_html_files = self._generate_html_report(func_profile_ref)

        report_params = {'message': '',
                         'objects_created': objects_created,
                         'workspace_id': workspace_id,
                         'html_links': output_html_files,
                         'direct_html_link_index': 0,
                         'html_window_height': 660,
                         'report_object_name': 'func_profile_viewer_' + str(uuid.uuid4())}

        kbase_report_client = KBaseReport(self.callback_url, token=self.token)
        output = kbase_report_client.create_extended_report(report_params)

        report_output = {'report_name': output['name'], 'report_ref': output['ref']}

        return report_output

    def _get_ids_from_amplicon_set(self, amplicon_set_ref):
        logging.info('start retrieving OTU ids from amplicon set')

        amplicon_set_data = self.dfu.get_objects(
                                            {'object_refs': [amplicon_set_ref]})['data'][0]['data']

        amplicons = amplicon_set_data.get('amplicons')

        return amplicons.keys()

    def _build_profile_data(self, profile_file_path, item_ids, profile_category, staging_file=False):

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
        if profile_category == 'community':
            unmatched_ids = set(item_ids) - set(df.columns)
            if unmatched_ids:
                msg = 'Found some unmatched set data ids in profile file columns\n{}'.format(
                                                                                    unmatched_ids)
                logging.warning(msg)

                unmatched_ids = set(item_ids) - set(df.index)
                if not unmatched_ids:
                    logging.warning('File index contains all items from sample set')
                    logging.warning('Using transpose matrix from file')
                    df = df.T
                else:
                    err_msg = 'Profile file does not contain all data ids from sample set'
                    raise ValueError(err_msg)
        else:
            unmatched_ids = set(item_ids) - set(df.index)
            if unmatched_ids:
                msg = 'Found some unmatched set data ids in profile file rows\n{}'.format(
                                                                                    unmatched_ids)
                logging.warning(msg)

                unmatched_ids = set(item_ids) - set(df.columns)
                if not unmatched_ids:
                    logging.warning('File columns contains all items from amplicon set')
                    logging.warning('Using transpose matrix from file')
                    df = df.T
                else:
                    err_msg = 'Profile file does not contain all data ids from amplicon set'
                    raise ValueError(err_msg)

        profile_data = {'row_ids': df.index.tolist(),
                        'col_ids': df.columns.tolist(),
                        'values': df.values.tolist()}

        return profile_data

    def _gen_func_profile(self, original_matrix_ref, amplicon_set_ref, sample_set_ref,
                          profile_category, profile_file_path, metadata, staging_file=False):

        func_profile_data = dict()

        func_profile_data.update(metadata)
        func_profile_data['original_matrix_ref'] = original_matrix_ref

        if profile_category not in PROFILE_CATEGORY:
            raise ValueError('Please choose community or organism as profile category')

        if profile_category == 'community':
            logging.info('start building community profile')
            if not sample_set_ref:
                raise ValueError('Please provide sample set object for community profile')
            func_profile_data['sample_set_ref'] = sample_set_ref
            func_profile_data.pop('row_attributemapping_ref', None)
            item_ids = self.sampleservice_util.get_ids_from_samples(sample_set_ref)

        if profile_category == 'organism':
            logging.info('start building organism profile')
            if not amplicon_set_ref:
                raise ValueError('Please provide amplicon set object for organism profile')
            func_profile_data['amplicon_set_ref'] = amplicon_set_ref
            func_profile_data.pop('col_attributemapping_ref', None)
            item_ids = self._get_ids_from_amplicon_set(amplicon_set_ref)

        profile_data = self._build_profile_data(profile_file_path, item_ids, profile_category,
                                                staging_file=staging_file)
        func_profile_data['data'] = profile_data

        return func_profile_data

    def __init__(self, config):
        self.callback_url = config['SDK_CALLBACK_URL']
        self.scratch = config['scratch']
        self.token = config['KB_AUTH_TOKEN']
        self.dfu = DataFileUtil(self.callback_url)
        self.report_util = kb_GenericsReport(self.callback_url)
        self.sampleservice_util = SampleServiceUtil(config)

        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)

    def import_func_profile(self, params):

        logging.info("start importing FunctionalProfile with params:{}".format(params))

        self._validate_params(params, ('workspace_id',
                                       'func_profile_obj_name',
                                       'original_matrix_ref',
                                       'profile_type',
                                       'profile_category',
                                       'profile_file_path'),
                                      ('data_epistemology',
                                       'epistemology_method',
                                       'description',
                                       'staging_file',
                                       'build_report'))

        workspace_id = params.get('workspace_id')
        func_profile_obj_name = params.get('func_profile_obj_name')
        staging_file = params.get('staging_file', False)
        build_report = params.get('build_report', False)
        profile_file_path = params.get('profile_file_path')

        original_matrix_ref = params.get('original_matrix_ref')
        matrix_data = self.dfu.get_objects(
                                            {'object_refs': [original_matrix_ref]})['data'][0]['data']

        amplicon_set_ref = matrix_data.get('amplicon_set_ref')
        sample_set_ref = matrix_data.get('sample_set_ref')
        params['col_attributemapping_ref'] = matrix_data.get('col_attributemapping_ref')
        params['row_attributemapping_ref'] = matrix_data.get('row_attributemapping_ref')

        profile_category = params.get('profile_category', '').lower()
        profile_type = params.get('profile_type', '').lower()

        metadata = dict()
        meta_fields = ['profile_category', 'profile_type',
                       'data_epistemology', 'epistemology_method', 'description',
                       'col_attributemapping_ref', 'row_attributemapping_ref']
        for meta_field in meta_fields:
            field_value = params.get(meta_field)
            if field_value:
                metadata[meta_field] = field_value

        if profile_type not in PROFILE_TYPE:
            raise ValueError('Please choose one of {} as profile type'.format(PROFILE_TYPE))

        func_profile_data = self._gen_func_profile(original_matrix_ref,
                                                   amplicon_set_ref,
                                                   sample_set_ref,
                                                   profile_category,
                                                   profile_file_path,
                                                   metadata,
                                                   staging_file=staging_file)

        func_profile_ref = self._save_func_profile(workspace_id,
                                                   func_profile_data,
                                                   func_profile_obj_name)

        returnVal = {'func_profile_ref': func_profile_ref}

        if build_report:
            report_output = self._gen_func_profile_report(func_profile_ref, workspace_id)
            returnVal.update(report_output)

        return returnVal
