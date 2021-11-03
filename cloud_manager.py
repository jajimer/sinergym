import argparse
from time import sleep
from pprint import pprint
import sinergym.utils.gcloud as gcloud
from google.cloud import storage
import google.api_core.exceptions

parser = argparse.ArgumentParser(
    description='Process for run experiments in Google Cloud')
parser.add_argument(
    '--project_id',
    '-id',
    type=str,
    dest='project',
    help='Your Google Cloud project ID.')
parser.add_argument(
    '--zone',
    '-zo',
    type=str,
    default='europe-west1-b',
    dest='zone',
    help='service Engine zone to deploy to.')
parser.add_argument(
    '--template_name',
    '-tem',
    type=str,
    default='sinergym-template',
    dest='template_name',
    help='Name of template previously created in gcloud account to generate VM copies.')
parser.add_argument(
    '--group_name',
    '-group',
    type=str,
    default='sinergym-group',
    dest='group_name',
    help='Name of instance group(MIG) will be created during experimentation.')
parser.add_argument(
    '--experiment_commands',
    '-cmds',
    default=['python3 ./algorithm/DQN.py -env Eplus-demo-v1 -ep 1 -'],
    nargs='+',
    dest='commands',
    help='list of commands for DRL_battery.py you want to execute remotely.')

args = parser.parse_args()

print('Init Google cloud service API...')
service = gcloud.init_gcloud_service()

print('Init Google Cloud Storage Client...')
client = gcloud.init_storage_client()

# Create instance group
n_experiments = len(args.commands)
print('Creating instance group(MIG) for experiments ({} instances)...'.format(
    n_experiments))
response = gcloud.create_instance_group(
    service=service,
    project=args.project,
    zone=args.zone,
    size=n_experiments,
    template_name=args.template_name,
    group_name=args.group_name)
pprint(response)

# Wait for the machines to be fully created.
print(
    '{0} status is {1}.'.format(
        response['operationType'],
        response['status']))
if response['status'] != 'DONE':
    response = gcloud.wait_for_operation(
        service,
        args.project,
        args.zone,
        operation=response['id'],
        operation_type=response['operationType'])
pprint(response)
print('MIG created.')

# If storage exists it will be used, else it will be created previously by API
print('Looking for experiments storage')
try:
    bucket = gcloud.get_bucket(client, bucket_name='experiments-storage')
    print(
        'Bucket {} found, this storage will be used when experiments finish.'.format(
            bucket.name))
except(google.api_core.exceptions.NotFound):
    print('Any bucket found into your Google account, generating new one...')
    bucket = gcloud.create_bucket(
        client,
        bucket_name='experiments-storage',
        location='EU')


# List VM names
print('Looking for instance names... (waiting for they are visible too)')
# Sometimes, although instance group insert status is DONE, isn't visible
# for API yet. Hence, we have to wait for with a loop...
instances = []
while len(instances) < n_experiments:
    instances = gcloud.list_instances(
        service=service,
        project=args.project,
        zone=args.zone,
        base_instances_names=args.group_name)
    sleep(3)
print(instances)
# Number of machines should be the same than commands

# Processing commands and adding group id to the petition
for i in range(len(args.commands)):
    args.commands[i] += ' --group_name ' + args.group_name

# Execute a comand in every container inner VM
print('Sending commands to every container VM... (waiting for container inner VM is ready too)')
for i, instance in enumerate(instances):
    container_id = None
    # Obtain container id inner VM
    while not container_id:
        container_id = gcloud.get_container_id(instance_name=instance)
        sleep(5)
    # Execute command in container
    gcloud.execute_remote_command_instance(
        container_id=container_id,
        instance_name=instance,
        experiment_command=args.commands[i])
    print(
        'command {} has been sent to instance {}(container: {}).'.format(
            args.commands[i],
            instance,
            container_id))

print('All VM\'s are working correctly, see Google Cloud Platform Console.')
