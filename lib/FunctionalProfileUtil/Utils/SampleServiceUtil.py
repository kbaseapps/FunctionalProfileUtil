
import json
import requests
import uuid
import logging

from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.SampleServiceClient import SampleService


class SampleServiceUtil:

    def __init__(self, config):
        self.callback_url = config['SDK_CALLBACK_URL']
        self.scratch = config['scratch']
        self.token = config['KB_AUTH_TOKEN']
        self.srv_wiz_url = config['srv-wiz-url']
        self.sample_url = config.get('kbase-endpoint') + '/sampleservice'
        self.dfu = DataFileUtil(self.callback_url)
        self.sample_ser = SampleService(self.sample_url)

        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)

    def get_sample_service_url(self):
        return self.sample_url

    def get_sample(self, sample_id, version=None):

        sample_url = self.get_sample_service_url()
        headers = {"Authorization": self.token}
        params = {
            "id": sample_id,
            "version": version
        }
        payload = {
            "method": "SampleService.get_sample",
            "id": str(uuid.uuid4()),
            "params": [params],
            "version": "1.1"
        }
        resp = requests.post(url=sample_url, headers=headers, data=json.dumps(payload))
        resp_json = resp.json()
        if resp_json.get('error'):
            raise RuntimeError(f"Error from SampleService - {resp_json['error']}")
        sample = resp_json['result'][0]

        # sample = self.sample_ser.get_sample(params)[0]

        return sample

    def get_ids_from_samples(self, sample_set_ref):
        logging.info('start retrieving sample ids from sample set')

        sample_set = self.dfu.get_objects(
                    {"object_refs": [sample_set_ref]})['data'][0]['data']

        samples = sample_set['samples']

        data_ids = []
        for sample in samples:
            sample_id = sample.get('id')
            version = sample.get('version')

            sample_data = self.get_sample(sample_id, version=version)

            data_id = sample_data['name']
            data_ids.append(data_id)

        return data_ids
