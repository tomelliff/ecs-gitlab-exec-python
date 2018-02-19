import boto3
import docker

ec2 = boto3.resource('ec2')
ecs_client = boto3.client('ecs')


def register_task_definition():
    task_family = 'tom-test'
    network_mode = 'bridge'

    container_name = 'tom-test'
    image = 'alpine'

    response = ecs_client.register_task_definition(
        family=task_family,
        networkMode=network_mode,
        containerDefinitions=[
            {
                'name': container_name,
                'image': image,
                'memoryReservation': 128,
                'command': [
                    'sh',
                ],
                'environment': [
                    {
                        'name': 'foo',
                        'value': 'bar'
                    },
                ]
            },
        ]
    )

    return response['taskDefinition']['taskDefinitionArn']


def run_task(task_definition, cluster):
    gitlab_ci_runner_name = 'foobar'

    response = ecs_client.run_task(
        cluster=cluster,
        taskDefinition=task_definition,
        overrides={
            'containerOverrides': [
                {
                    'environment': [
                        {
                            'name': 'foo',
                            'value': 'baz'
                        },
                    ]
                }
            ]
        },
        count=1,
        startedBy=gitlab_ci_runner_name,
    )

    task = response['tasks'][0]
    task_arn = task['taskArn']
    container_instance_arn = task['containerInstanceArn']

    return task_arn, container_instance_arn


def get_instance_id(cluster, container_instance_arn):
    response = ecs_client.describe_container_instances(
        cluster=cluster,
        containerInstances=[
            container_instance_arn,
        ]
    )

    return response['containerInstances'][0]['ec2InstanceId']


def get_instance_ip(instance_id, private_ip=True):
    instance = ec2.Instance(instance_id)

    if private_ip:
        return instance.attributes.get('private_ip_address')
    else:
        return instance.attributes.get('public_ip_address')


def exec_remote_container(remote_url, container, command):
    client = docker.DockerClient(base_url=remote_url, version='auto')
    container = client.containers.get(container)
    return container.exec_run(command)


def stop_task(cluster, task):
    ecs_client.stop_task(
        cluster=cluster,
        task=task,
    )


def run_job():
    task_definition_arn = register_task_definition()
    task_arn, container_instance_arn = run_task(task_definition_arn, 'tom-test')
    ip_address = get_instance_ip(get_instance_id('tom-test', container_instance_arn))
    exec_remote_container('tcp://{}:2376'.format(ip_address), 'ls -la /')
    stop_task('tom-test', task_arn)
