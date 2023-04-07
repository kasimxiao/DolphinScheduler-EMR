# DolphinScheduler EMR任务调度

## 前言

随着企业规模的扩大，业务数据的激增，我们会使用Hadoop/Spark框架来处理大量数据的ETL/聚合分析作业，而这些作业将需要由统一的作业调度平台去定时调度。

在Amazon EMR中，可以使用AWS提供Setp Function，托管AirFlow，以及Apache Oozie或Azkaban进行作业的调用。但随着Apache Dolphinscheduler产品完善、社区的火爆、普及率的提升，越来越多的企业使用该产品作为任务调度的服务。Dolphinscheduler可以在Amazon EMR单独的集群中进行安装和部署，但是结合Amazon EMR本身的特点，基于使用最佳实践，我们不建议客户使用一个大而全，并且持久运行的集群提供整个大数据的相关服务，而是基于不同的维度对集群进行拆分，比如研发阶段（开发、测试、生产）、工作负载（即席查询、批处理）、时间敏感、作业时长、组织类型等，因此Dolphinscheduler作为统一的调度平台，则不需要安装在某一个固定EMR集群上，而是选择单独部署，将作业以 DAG（Directed Acyclic Graph，DAG）流式方式组装，统一的调度和管理。

![Untitled](/image/Untitled.png)

此篇文章将介绍DolphinScheduler安装部署，以及使用python脚本的方式执行EMR的任务调度，包括集群创建、集群状态检查、作业创建、作业状态检查，所有任务完成后集群自动销毁。

## Amazon EMR

[Amazon EMR](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-what-is-emr.html)是一个托管的集群平台，可简化在AWS上运行大数据框架（如 Apache Hadoop 和 Apache Spark）的过程，以处理和分析海量数据。用户可一键启动包含了众多 Hadoop 生态数据处理，分析相关服务的集群，而无需手动进行复杂的配置。

## Apache Dolphinscheduler

[Apache DolphinScheduler](https://dolphinscheduler.apache.org/zh-cn/docs/3.1.4/about/introduction) 是一个分布式易扩展的可视化DAG工作流任务调度开源系统。适用于企业级场景，提供了一个可视化操作任务、工作流和全生命周期数据处理过程的解决方案。

架构图：
![Untitled](/image/Untitled%201.png)

主要可实现：

- 以 DAG 图的方式将 Task 按照任务的依赖关系关联起来，可实时可视化监控任务的运行状态
- 支持丰富的任务类型：Shell、MR、Spark、SQL(mysql、oceanbase、postgresql、hive、sparksql)、Python、Sub_Process、Procedure 等
- 支持工作流定时调度、依赖调度、手动调度、手动暂停/停止/恢复，同时支持失败重试/告警、从指定节点恢复失败、Kill 任务等操作
- 支持工作流优先级、任务优先级及任务的故障转移及任务超时告警/失败
- 支持工作流全局参数及节点自定义参数设置
- 支持资源文件的在线上传/下载，管理等，支持在线文件创建、编辑
- 支持任务日志在线查看及滚动、在线下载日志等
- 实现集群 HA，通过 Zookeeper 实现 Master 集群和 Worker 集群去中心化
- 支持对Master/Worker cpu load，memory，cpu 在线查看
- 支持工作流运行历史树形/甘特图展示、支持任务状态统计、流程状态统计
- 支持补数
- 支持多租户
- 支持国际化

## 安装DolphinScheduler

DolphinScheduler支持多种部署方式
- 单机部署：Standalone 仅适用于 DolphinScheduler 的快速体验.
- 伪集群部署：伪集群部署目的是在单台机器部署 DolphinScheduler 服务，该模式下master、worker、api server 都在同一台机器上
- 集群部署：集群部署目的是在多台机器部署 DolphinScheduler 服务，用于运行大量任务情况。

如果你是新手，想要体验 DolphinScheduler的功能，推荐使用Standalone方式体检。如果你想体验更完整的功能，或者更大的任务量，推荐使用伪集群部署。如果你是在生产中使用，推荐使用集群部署或者kubernetes

本次实验提供伪集群在aws上部署完整部署方式，请见[部署详情](https://github.com/kasimxiao/DolphinScheduler-EMR/tree/main/DolphinScheduler-Deploy)

## 配置DolphinScheduler

**1、建立租户**

![Untitled](/image/Untitled%204.png)

2、用户绑定租户

![Untitled](/image/Untitled%205.png)

**3、AWS创建IAM 策略**

进入AWS IAM，创建调用EMR服务的策略
替换EMR_DefaultRole和EMR_EC2_DefaultRole，为你EMR创建时选择的角色
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ElasticMapReduceActions",
            "Effect": "Allow",
            "Action": [
                "elasticmapreduce:RunJobFlow",
                "elasticmapreduce:DescribeCluster",
                "elasticmapreduce:AddJobFlowSteps",
                "elasticmapreduce:DescribeStep",
                "elasticmapreduce:TerminateJobFlows",
                "elasticmapreduce:SetTerminationProtection"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetRole",
                "iam:PassRole"
            ],
            "Resource": [
                "arn:aws:iam::accountid:role/EMR_DefaultRole",
                "arn:aws:iam::accountid:role:role/EMR_EC2_DefaultRole"
            ]
        }
    ]
}
```

**4、创建IAM 角色**

进入AWS IAM，创建角色，并赋予上一步所创建的策略

**5、DolphinScheduler部署EC2绑定角色**

将EC2绑定上一步创建的角色，使DolphinScheduler所部署EC2具有调用EMR权限

![Untitled](/image/Untitled%206.png)

![Untitled](/image/Untitled%207.png)

**6、python 安装boto3，以及要用到其他的组件**

```bash
sudu pip install boto3
sudu pip install Redis
```

## 使用DolphinScheduler提交作业-以python方式执行

### 路径：项目管理-工作流定义-创建

**1、创建EMR集群创建任务**

创建一个EMR集群，3个MASTER，3个CORE，指定子网与权限，以及集群空闲十分中自动终止
具体参数可见[链接](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/emr/client/run_job_flow.html)


```python
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
            #替换{Sunbet-id}为你需要部署的子网id
            'Ec2SubnetId': '{Sunbet-id}',
            #替换{Keypairs-name}为你ec2使用密钥对名称
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
```

**2、创建EMR集群状态检查任务**

**检查集群是否创建完毕**

```python
import boto3
import redis
import time
from datetime import date

if __name__ == "__main__":
    today = date.today()
    d1 = today.strftime("%Y%m%d")

    #{region}替换为你需要创建EMR的Region
    client = boto3.client('emr',region_name='{region}')
    #替换{redis-endpoint}为你redis连接地址
    pool = redis.ConnectionPool(host='{redis-endpoint}', port=6379, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    #获取创建创建的EMR集群id
    job_id = r.get('cluster_id_' + d1)
    print(job_id)
    while True:
        result = client.describe_cluster(ClusterId=job_id)
        emr_state = result['Cluster']['Status']['State']
        print(emr_state)
        if emr_state == 'WAITING':
            #EMR集群创建成功
            break
        elif emr_state == 'FAILED':
            #集群创建失败
            #do something...
            break
        else:
            time.sleep(10)
```

**3、使用创建好的集群启动spark job**

```python
import time
import re
import boto3
from datetime import date
import redis

def generate_step(step_name, step_command):
    cmds = re.split('\\s+', step_command)
    print(cmds)
    if not cmds:
        raise ValueError
    return {
        'Name': step_name,
        'ActionOnFailure': 'CANCEL_AND_WAIT',
        'HadoopJarStep': {
            'Jar': 'command-runner.jar',
            'Args': cmds
        }
    }

def add_job_flow_steps(steps, flow_id=None):
        return client.add_job_flow_steps(JobFlowId=flow_id, Steps=steps)

if __name__ == "__main__":
    today = date.today()
    d1 = today.strftime("%Y%m%d")

    #{region}替换为你需要创建EMR的Region
    client = boto3.client('emr',region_name='{region}')
	
    #获取emr集群id
    #替换{redis-endpoint}为你redis连接地址
    pool = redis.ConnectionPool(host='{redis-endpoint}', port=6379, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    job_id = r.get('cluster_id_' + d1)

	#job启动命令
    spark_submit_cmd = """spark-submit
                s3://s3bucket/file/spark/spark-etl.py
                s3://s3bucket/input/
                s3://s3bucket/output/spark/"""+d1+'/'

    steps = []
    steps.append(generate_step("SparkExample_"+d1 , spark_submit_cmd),)
    #提交EMR Step作业
    response = client.add_job_flow_steps(JobFlowId=job_id, Steps=steps)
    step_id = response['StepIds'][0]
    #将作业id保存，以便于做任务检查
    r.set('SparkExample_'+d1, step_id)
```

**4、创建JOB执行情况检查**

```python
import boto3
import redis
import time
from datetime import date

def describe_step(job_id,step_id):
    return client.describe_step(ClusterId=job_id,StepId=step_id)

if __name__ == "__main__":
    today = date.today()
    d1 = today.strftime("%Y%m%d")

    #{region}替换为你需要创建EMR的Region
    client = boto3.client('emr',region_name='{region}')

    #替换{redis-endpoint}为你redis连接地址
    pool = redis.ConnectionPool(host='{redis-endpoint}', port=6379, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    job_id = r.get('cluster_id_' + d1)
    step_id = r.get('SparkExample_' + d1)
    print(job_id)
    print(step_id)

    while True:
        #查询作业执行结果
        result = describe_step(job_id, step_id)
        emr_state = result['Step']['Status']['State']
        print(emr_state)
        if emr_state == 'COMPLETED':
            #作业执行完成
            break
        elif emr_state == 'FAILED'
            #作业执行失败
            #do somethine
            #......
            break
        else:
            time.sleep(10)
```

**5、设置执行顺序**

![Untitled](/image/Untitled%208.png)
在DolphinScheduler-项目管理-工作流-工作流定义中创建工作流，并创建python任务，将以上python脚本作为任务串联起来

**6、保存并上线**

![Untitled](/image/Untitled%209.png)
保存任务并点击上线

**7、执行**

可以点击立即执行，或指定计划任务按时执行
![Untitled](/image/Untitled%2010.png)

在EMR中查看执行情况
EMR创建中
![Untitled](/image/Untitled%2014.png)
Setp执行中
![Untitled](/image/Untitled%2015.png)

**8、检查执行结果以及执行日志**

在DolphinScheduler-项目管理-工作流-工作流实例中检查执行状态，以及执行日志
![Untitled](/image/Untitled%2011.png)
![Untitled](/image/Untitled%2012.png)

在EMR中查看执行情况
EMR创建完成
![Untitled](/image/Untitled%2017.png)
Setp执行完成
![Untitled](/image/Untitled%2016.png)

**9、终止集群**

对于临时性执行作业或者每天定时执行的批处理作业，可以在作业结束后终止EMR集群以节省成本（EMR使用最佳实践）。
终止EMR集群可以使用EMR本身功能在空闲后自动终止，或者手动调用终止。
自动终止EMR集群：

```bash
#在创建EMR集群的run_job_flow模板中加入：
AutoTerminationPolicy={
    'IdleTimeout': 600
}
```
此集群将在作业执行完空闲十分钟后自动终止
手动终止EMR集群：
```python
import boto3
from datetime import date
import redis

if __name__ == "__main__":
    today = date.today()
    d1 = today.strftime("%Y%m%d")

    #获取集群id
    #{region}替换为你需要创建EMR的Region
    client = boto3.client('emr',region_name='{region}')

    #替换{redis-endpoint}为你redis连接地址
    pool = redis.ConnectionPool(host='{redis-endpoint}', port=6379, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    job_id = r.get('cluster_id_' + d1)
    #关闭集群终止保护
    client.set_termination_protection(JobFlowIds=[job_id],TerminationProtected=False)
    #终止集群
    client.terminate_job_flows(JobFlowIds=[job_id])
```
将此脚本加入到DolphinScheduler 作业流中，作业流在全部任务执行完成后执行该脚本以实现终止EMR集群

## 使用DolphinScheduler提交作业-以shell方式提交

1、将python代码保存到服务器

2、创建shell脚本工作流，执行python

```bash
python ~/dolphinscheduler/script/createcluster.py
```
![Untitled](/image/Untitled%2013.png)

3、保存/上线/执行/检查

执行结果相同

## 总结

通过独立部署Dolphinscheduler，利用Amazon EMR特性，客户可以根据自身特性/需求自定义分离负载操作，使用既有集群或创建瞬时集群，进行作业的调度和编排，并制定定时计划任务。