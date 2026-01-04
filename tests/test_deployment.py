
import unittest
import json
import yaml

class TestDeployment(unittest.TestCase):
    def test_deployment_manifest(self):
        with open('project_tracking/config.json', 'r') as f:
            config = json.load(f)

        with open('deploy.yaml', 'r') as f:
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
