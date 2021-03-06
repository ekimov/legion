#
#    Copyright 2017 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
from __future__ import print_function

import unittest2
import json
from random import randint
import urllib.parse
from io import BytesIO
from werkzeug.datastructures import FileMultiDict


try:
    from .legion_test_utils import patch_environ, ModelServeTestBuild
    from .legion_test_models import create_simple_summation_model_by_df, \
        create_simple_summation_model_by_types, create_simple_summation_model_untyped, \
        create_simple_summation_model_by_df_with_prepare, create_simple_summation_model_lists, \
        create_simple_summation_model_lists_with_files_info
except ImportError:
    from legion_test_utils import patch_environ, ModelServeTestBuild
    from legion_test_models import create_simple_summation_model_by_df, \
        create_simple_summation_model_by_types, create_simple_summation_model_untyped, \
        create_simple_summation_model_by_df_with_prepare, create_simple_summation_model_lists, \
        create_simple_summation_model_lists_with_files_info

import legion.serving.pyserve as pyserve


class TestModelApiEndpoints(unittest2.TestCase):
    MODEL_ID = 'temp'
    MODEL_VERSION = '1.8'

    @staticmethod
    def _load_response_text(response):
        data = response.data

        if isinstance(data, bytes):
            data = data.decode('utf-8')

        return data

    def _parse_json_response(self, response):
        self.assertEqual(response.mimetype, 'application/json', 'Invalid response mimetype')

        data = self._load_response_text(response)
        return json.loads(data)

    def test_health_check(self):
        with ModelServeTestBuild(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            response = model.client.get(pyserve.SERVE_HEALTH_CHECK)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(self._load_response_text(response), 'OK')

    def test_model_info_with_df(self):
        with ModelServeTestBuild(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            response = model.client.get(pyserve.SERVE_INFO.format(model_id=self.MODEL_ID))
            data = self._parse_json_response(response)

            self.assertIsInstance(data, dict, 'Data is not a dictionary')
            self.assertTrue('version' in data, 'Cannot find version field')
            self.assertTrue('use_df' in data, 'Cannot find use_df field')
            self.assertTrue('input_params' in data, 'Cannot find input_params field')

            self.assertEqual(data['version'], self.MODEL_VERSION, 'Incorrect model version')
            self.assertEqual(data['use_df'], True, 'Incorrect model use_df field')
            self.assertDictEqual(data['input_params'],
                                 {'b': {'numpy_type': 'int64', 'type': 'Integer'},
                                  'a': {'numpy_type': 'int64', 'type': 'Integer'}},
                                 'Incorrect model input_params')

    def test_model_info_with_typed_columns(self):
        with ModelServeTestBuild(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_by_types) as model:
            response = model.client.get(pyserve.SERVE_INFO.format(model_id=self.MODEL_ID))
            data = self._parse_json_response(response)

            self.assertIsInstance(data, dict, 'Data is not a dictionary')
            self.assertTrue('version' in data, 'Cannot find version field')
            self.assertTrue('use_df' in data, 'Cannot find use_df field')
            self.assertTrue('input_params' in data, 'Cannot find input_params field')

            self.assertEqual(data['version'], self.MODEL_VERSION, 'Incorrect model version')
            self.assertEqual(data['use_df'], False, 'Incorrect model use_df field')
            self.assertDictEqual(data['input_params'],
                                 {'b': {'numpy_type': 'int32', 'type': 'Integer'},
                                  'a': {'numpy_type': 'int32', 'type': 'Integer'}},
                                 'Incorrect model input_params')

    def test_model_info_with_untyped_columns(self):
        with ModelServeTestBuild(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_untyped) as model:
            response = model.client.get(pyserve.SERVE_INFO.format(model_id=self.MODEL_ID))
            data = self._parse_json_response(response)

            self.assertIsInstance(data, dict, 'Data is not a dictionary')
            self.assertTrue('version' in data, 'Cannot find version field')
            self.assertTrue('use_df' in data, 'Cannot find use_df field')
            self.assertTrue('input_params' in data, 'Cannot find input_params field')

            self.assertEqual(data['version'], self.MODEL_VERSION, 'Incorrect model version')
            self.assertEqual(data['use_df'], False, 'Incorrect model use_df field')
            self.assertEqual(data['input_params'], False, 'Incorrect model input_params')

    def test_model_invoke_summation_with_df(self):
        with ModelServeTestBuild(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            a = randint(1, 1000)
            b = randint(1, 1000)

            response = model.client.get(pyserve.SERVE_INVOKE.format(model_id=self.MODEL_ID) + '?a={}&b={}'.format(a, b))
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'x': a + b})

    def test_model_invoke_summation_with_df_and_get_post_method(self):
        with ModelServeTestBuild(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            a = randint(1, 1000)
            b = randint(1, 1000)

            response = model.client.post(pyserve.SERVE_INVOKE.format(model_id=self.MODEL_ID) + '?a={}'.format(a),
                                         data={'b': b})
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'x': a + b})

    def test_model_invoke_summation_with_df_and_files(self):
        with ModelServeTestBuild(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df) as model:
            a = randint(1, 1000)
            b = randint(1, 1000)

            response = model.client.post(pyserve.SERVE_INVOKE.format(model_id=self.MODEL_ID),
                                         data={
                                             'a': (BytesIO(str(a).encode('utf-8')), 'random file name a.txt'),
                                             'b': (BytesIO(str(b).encode('utf-8')), 'random file name b.txt')
                                         })
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'x': a + b})

    def test_model_invoke_summation_with_df_with_prepare(self):
        with ModelServeTestBuild(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_by_df_with_prepare) as model:
            a = randint(1, 1000)
            b = randint(1, 1000)

            response = model.client.get(pyserve.SERVE_INVOKE.format(model_id=self.MODEL_ID) + '?a={}&b={}'.format(a, b))
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'x': a + b})

    def test_model_invoke_summation_with_typed_columns(self):
        with ModelServeTestBuild(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_by_types) as model:
            a = randint(1, 1000)
            b = randint(1, 1000)

            response = model.client.get(pyserve.SERVE_INVOKE.format(model_id=self.MODEL_ID) + '?a={}&b={}'.format(a, b))
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'x': a + b})

    def test_model_invoke_summation_with_untyped_columns(self):
        with ModelServeTestBuild(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_untyped) as model:

            payload = {
                'var_b': randint(1, 1000),
                'var_a': randint(1, 1000),
                'var_c': randint(1, 1000)
            }

            payload_string = '?' + urllib.parse.urlencode(payload)
            response = model.client.get(pyserve.SERVE_INVOKE.format(model_id=self.MODEL_ID)
                                        + payload_string)
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'keys': 'var_a,var_b,var_c', 'sum': sum(payload.values())})

    def test_model_invoke_summation_with_untyped_columns_and_lists(self):
        with ModelServeTestBuild(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_lists) as model:

            payload = {
                'movies': ['Titanic', 'Avatar', 'Pulp_Fiction'],
                'ratings': [4, 3, 5]
            }

            payload_string = '?'
            payload_string += '&'.join('movie[]=' + str(value) for value in payload['movies'])
            payload_string += '&' + '&'.join('rate[]=' + str(value) for value in payload['ratings'])

            response = model.client.get(pyserve.SERVE_INVOKE.format(model_id=self.MODEL_ID)
                                        + payload_string)
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'worth': 'Avatar', 'best': 'Pulp_Fiction'})

    def test_model_invoke_summation_with_untyped_columns_and_lists_with_files_info(self):
        with ModelServeTestBuild(self.MODEL_ID, self.MODEL_VERSION,
                                 create_simple_summation_model_lists_with_files_info) as model:

            films = {
                'Titanic': 4,
                'Avatar': 3,
                'Pulp_Fiction': 5,
            }

            files = FileMultiDict()
            for film, rate in films.items():
                content = '{}\n{}'.format(film, rate)
                file_name = 'random file name {}.txt'.format(film)

                files.add('file[]', (BytesIO(str(content).encode('utf-8')), file_name))

            response = model.client.post(pyserve.SERVE_INVOKE.format(model_id=self.MODEL_ID), data=files)
            result = self._parse_json_response(response)

            self.assertIsInstance(result, dict, 'Result not a dict')
            self.assertDictEqual(result, {'worth': 'Avatar', 'best': 'Pulp_Fiction'})


if __name__ == '__main__':
    unittest2.main()
