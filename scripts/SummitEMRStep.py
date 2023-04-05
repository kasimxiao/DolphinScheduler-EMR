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