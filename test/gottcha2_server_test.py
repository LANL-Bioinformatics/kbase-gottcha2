# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser
import subprocess
import logging
from pprint import pprint

from gottcha2.gottcha2Impl import gottcha2
from gottcha2.gottcha2Server import MethodContext
from gottcha2.authclient import KBaseAuth as _KBaseAuth

from installed_clients.WorkspaceClient import Workspace
from installed_clients.ReadsUtilsClient import ReadsUtils


class gottcha2Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('gottcha2'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'gottcha2',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = gottcha2(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        suffix = int(time.time() * 1000)
        cls.wsName = "test_gottcha2_" + str(suffix)
        cls.ru = ReadsUtils(os.environ['SDK_CALLBACK_URL'])
        ret = cls.wsClient.create_workspace({'workspace': cls.wsName})  # noqa

    @classmethod
    def prepareTestData(cls):

        filename = os.path.join(cls.scratch, 'test.fastq')

        readsUtil = ReadsUtils.upload_reads(cls.callback_url)
        # cls.assembly_ref = readsUtil.({
        #     'file': {'path': filename},
        #     'workspace_name': cls.wsName,
        #     'assembly_name': 'TestAssembly'
        # })
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def getWsClient(self):
        return self.__class__.wsClient

    @staticmethod
    def get_file_paths(report_params):
        file_paths = []
        [file_paths.append(f['path']) for f in report_params['file_links']]
        return file_paths

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def test_params(self):
        # Prepare test objects in workspace if needed using
        # self.getWsClient().save_objects({'workspace': self.getWsName(),
        #                                  'objects': []})
        #
        # Run your method by
        # ret = self.getImpl().your_method(self.getContext(), parameters...)
        #
        # Check returned data with
        # self.assertEqual(ret[...], ...) or other unittest methods

        # Test ReadsSet two_se_reads_set
        result = self.serviceImpl.run_gottcha2(self.ctx, {'workspace_name': self.wsName,
                                                          'input_refs': ['22956/50/1'],
                                                          'db_type': 'RefSeq-r90.cg.Viruses.species.fna',
                                                          'min_coverage': 0.005
                                                          })[0]

        logging.info(f"report_ref {result['report_ref']}")
        self.assertIn('report_name', result)
        self.assertIn('report_ref', result)
        report = self.getWsClient().get_objects2({'objects': [{'ref': result['report_ref']}]})['data'][0]['data']
        logging.info(f'print report {report}')
        # pprint(report)
        logging.info(self.getWsClient().get_objects2({'objects': [{'ref': result['report_ref']}]})['data'])
        self.assertIn('direct_html', report)
        self.assertIn('file_links', report)
        self.assertIn('html_links', report)
        self.assertIn('objects_created', report)
        self.assertIn('text_message', report)
        # self.assertIn('gottcha2.gottcha_species.sam', report['html_links'])

        # test SingleEndLibrary test.fastq_reads
        # result = self.serviceImpl.run_gottcha2(self.ctx, {'workspace_name': self.wsName,
        #                                                'input_refs': ['22852/10/1'],
        #                                                'db_type': 'RefSeq-r90.cg.Viruses.species.fna',
        #                                                'min_coverage': 0.005
        #                                                })[0]
        # logging.info(f'{result}')

    # def DONOT_test_gottcha(self):
    #     self.assertTrue(os.path.exists('/data/gottcha2/RefSeq90'))
    #     self.assertTrue(os.path.exists('/data/gottcha2/RefSeq90/RefSeq-r90.cg.Viruses.species.fna.mmi'))
    #     output_dir = os.path.join(self.scratch, 'test_gottcha')
    #     # 'sh lib/gottcha2/src/uge-gottcha2.sh -i test/data/test.fastq -o test/data/output -p testing -d test/data/RefSeq-r90.cg.Viruses.species.fna'
    #     cmd = ['/kb/module/lib/gottcha2/src/uge-gottcha2.sh', '-i', '/data/gottcha2/RefSeq90/test.fastq', '-o', output_dir, '-p',
    #            'testing', '-d', '/data/gottcha2/RefSeq90/RefSeq-r90.cg.Viruses.species.fna']
    #     p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #     print(p.communicate())
    #     self.assertTrue(os.path.exists(os.path.join(output_dir, 'testing.summary.tsv')))
    #     self.assertTrue(os.path.exists(os.path.join(output_dir, 'testing.krona.html')))
    #     with open(os.path.join(output_dir, 'testing.summary.tsv'), 'r') as fp:
    #         logging.info('print summary')
    #         lines = fp.readlines()
    #         for line in lines:
    #             logging.info(line)
    #         self.assertTrue('Zaire ebolavirus' in lines[7])

