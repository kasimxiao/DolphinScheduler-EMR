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