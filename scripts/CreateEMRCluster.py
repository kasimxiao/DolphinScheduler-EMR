import boto3
from datetime import date
import redis

def run_job_flow():
    response = client.run_job_flow(
        Name='create-emrcluster-'+ d1,
        LogUri='s3://s3bucket/elasticmapreduce/',
        ReleaseLabel='emr-6.8.0',
        Instances={
            'KeepJobFlowAliveWhenNoSteps': False,
            'TerminationProtected': False,
            'Ec2SubnetId': '{Sunbet-id}',
            'Ec2KeyName': '{Keypairs-name}',
            'InstanceGroups': [
                {
                    'Name': 'Master',
                    'Market': 'ON_DEMAND',
                    'InstanceRole': 'MASTER',
                    'InstanceType': 'm5.xlarge',
                    'InstanceCount': 3,
                    'EbsConfiguration': {
                        'EbsBlockDeviceConfigs': [
                            {
                                'VolumeSpecification': {
                                    'VolumeType': 'gp3',
                                    'SizeInGB': 500
                                },
                                'VolumesPerInstance': 1
                            },
                        ],
                        'EbsOptimized': True
                    },
                },
                {
                    'Name': 'Core',
                    'Market': 'ON_DEMAND',
                    'InstanceRole': 'CORE',
                    'InstanceType': 'm5.xlarge',
                    'InstanceCount': 3,
                    'EbsConfiguration': {
                        'EbsBlockDeviceConfigs': [
                            {
                                'VolumeSpecification': {
                                    'VolumeType': 'gp3',
                                    'SizeInGB': 500
                                },
                                'VolumesPerInstance': 1
                            },
                        ],
                        'EbsOptimized': True
                    },
                }
            ],
        },
        Applications=[{'Name': 'Spark'},{'Name': 'Hive'},{'Name': 'Pig'},{'Name': 'Presto'}],
        Configurations=[
            { 'Classification': 'spark-hive-site',
                'Properties': {
                    'hive.metastore.client.factory.class': 'com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory'}
            },
            { 'Classification': 'hive-site',
                'Properties': {
                    'hive.metastore.client.factory.class': 'com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory'}
            },
            { 'Classification': 'presto-connector-hive',
                'Properties': {
                    'hive.metastore.glue.datacatalog.enabled': 'true'}
            }
        ],
        JobFlowRole='EMR_EC2_DefaultRole',
        ServiceRole='EMR_DefaultRole',
        EbsRootVolumeSize=100,
        #集群空闲十分钟自动终止
        AutoTerminationPolicy={
            'IdleTimeout': 600
        }
      )
    return response

if __name__ == "__main__":
    today = date.today()
    d1 = today.strftime("%Y%m%d")
    #{region}替换为你需要创建EMR的Region
    client = boto3.client('emr',region_name='{region}')
    #创建EMR集群
    clusterCreate = run_job_flow()
    job_id = clusterCreate['JobFlowId']
		
	#使用redis来保存信息，作为DolphinScheduler job step的参数传递，也可以使用DolphinScheduler所使用的mysql或者其他方式存储
    #替换{redis-endpoint}为你redis连接地址
    pool = redis.ConnectionPool(host='{redis-endpoint}', port=6379, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    r.set('cluster_id_'+d1, job_id)