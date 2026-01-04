import unittest
import json
import yaml
import os
import tempfile

class TestDeployment(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.tmpdir.name, 'config.json')
        self.deploy_path = os.path.join(self.tmpdir.name, 'deploy.yaml')
        
        # Create dummy config
        with open(self.config_path, 'w') as f:
            json.dump({'image': 'my-app:latest', 'port': 8080}, f)
            
        # Create dummy deployment manifest
        manifest = [
            {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'spec': {
                    'template': {
                        'spec': {
                            'containers': [{'name': 'app', 'image': 'my-app:latest', 'ports': [{'containerPort': 8080}]}]
                        }
                    }
                }
            },
            {
                'apiVersion': 'v1',
                'kind': 'Service',
                'spec': {
                    'ports': [{'port': 8080}]
                }
            }
        ]
        with open(self.deploy_path, 'w') as f:
            yaml.dump_all(manifest, f)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_deployment_manifest(self):
        with open(self.config_path, 'r') as f:
            config = json.load(f)

        with open(self.deploy_path, 'r') as f:
            deployment = list(yaml.safe_load_all(f))

        # Check Deployment
        deployment_spec = deployment[0]['spec']['template']['spec']['containers'][0]
        self.assertEqual(deployment_spec['image'], config['image'])
        self.assertEqual(deployment_spec['ports'][0]['containerPort'], config['port'])

        # Check Service
        service_spec = deployment[1]['spec']['ports'][0]
        self.assertEqual(service_spec['port'], config['port'])

if __name__ == '__main__':
    unittest.main()
