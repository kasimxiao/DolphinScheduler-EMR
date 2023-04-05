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