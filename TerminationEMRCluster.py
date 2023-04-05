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
    
	client.set_termination_protection(JobFlowIds=[job_id],TerminationProtected=False)
    client.terminate_job_flows(JobFlowIds=[job_id])