# 安装DolphinScheduler

本实验使用单实例伪集群部署方式

**1、启动一台EC2**

在在公有public subnet，选用amazon-linux2，m5.xlarge
安全组开启tcp 12345端口，0.0.0.0/0

**2、EC2安装JDK，配置JAVA_HOME环境**

```bash
yum search java | grep jdk
yum install java-1.8.0-openjdk-devel.x86_64
#配置环境变量
ll /usr/lib/jvm
vi /etc/profile
```
修改环境变量，增加如下配置
```bash
#set java environment
JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.362.b08-1.amzn2.0.1.x86_64
JRE_HOME=$JAVA_HOME/jre
CLASS_PATH=.:$JAVA_HOME/lib/dt.jar:$JAVA_HOME/lib/tools.jar:$JRE_HOME/lib
PATH=$PATH:$JAVA_HOME/bin:$JRE_HOME/bin
export JAVA_HOME JRE_HOME CLASS_PATH PATH
```
更新并检查java环境
```bash
source /etc/profile
java -version
```

**3、下载DolphinScheduler**

```bash
cd /usr/local/src
wget https://dlcdn.apache.org/dolphinscheduler/3.1.4/apache-dolphinscheduler-3.1.4-bin.tar.gz
```

**4、安装ZooKeeper**

```bash
cd /usr/local/src
wget https://dlcdn.apache.org/zookeeper/zookeeper-3.8.1/apache-zookeeper-3.8.1-bin.tar.gz
tar -zxvf apache-zookeeper-3.8.1-bin.tar.gz
cd apache-zookeeper-3.8.1-bin
# 创建数据存储目录
mkdir data
# 创建日志存储目录
mkdir logs
cd conf
# 配置文件拷贝
cp zoo_sample.cfg zoo.cfg

vi zoo.cfg
```
修改zoo.cfg配置
```bash
dataDir=/opt/zookeeper/data
dataLogDir=/opt/zookeeper/logs
```
启动/查看zookkeeper
```bash
cd ../
#启动
bin/zkServer.sh status
#查看状态
bin/zkServer.sh status
```

![Untitled](/image/Untitled%202.png)

**5、部署数据库，这里选用的Aurora serverless**

![Untitled](/image/Untitled%203.png)

安全组设置允许DolphinScheduler EC2所在安全组3306访问

**6、安装AWS CLI2**

```bash
yum remove awscli -y
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

vi /etc/profile
```
修改环境变量，增加如下配置
```bash
export PATH=$PATH:/usr/local/bin
```
更新环境变量
```bash
source /etc/profile
```
**7、更新python版本到3.9**

```bash
yum install gcc
cd /usr/local/src
wget https://www.python.org/ftp/python/3.9.1/Python-3.9.1.tgz
tar -zxvf
mkdir  /usr/local/python3/
cd Python-3.9.1
./configure --prefix=/usr/local/python3
make && make install

#把centos旧的python版本移走
mv /usr/bin/python /usr/bin/python_old
mv /usr/bin/pip /usr/bin/pip_old

ln -s /usr/local/python3/bin/python3.9 /usr/bin/python
ln -s /usr/local/python3/bin/pip3.9 /usr/bin/pip
```

修改yum使用python版本
```bash
#yum需要用来老版本
vi /usr/bin/yum
#!/usr/bin/python2.7 -> #!/usr/bin/python_old
vi /usr/libexec/urlgrabber-ext-down
#!/usr/bin/python2.7 -> #!/usr/bin/python_old
```

**8、配置用户免密及权限**

```bash
# 创建用户需使用 root 登录
useradd dolphinscheduler

# 添加密码
echo "dolphinscheduler" | passwd --stdin dolphinscheduler

# 配置 sudo 免密
sed -i '$adolphinscheduler  ALL=(ALL)  NOPASSWD: NOPASSWD: ALL' /etc/sudoers
sed -i 's/Defaults    requirett/#Defaults    requirett/g' /etc/sudoers

# 修改目录权限，使得部署用户对二进制包解压后的 apache-dolphinscheduler-*-bin 目录有操作权限
cd /usr/local/src
chown -R dolphinscheduler:dolphinscheduler apache-dolphinscheduler-*-bin
```

**9、配置机器SSH免密登录**

```bash
#切换dolphinscheduler用户
su dolphinscheduler

ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```
注意: 配置完成后，可以通过运行命令 ssh localhost 判断是否成功，如果不需要输入密码就能ssh登陆则证明成功

**10、数据初始化**

```bash

cd /usr/local/src
#下载mysql-connector
wget https://downloads.mysql.com/archives/get/p/3/file/mysql-connector-j-8.0.31.tar.gz
tar -zxvf mysql-connector-j-8.0.31.tar.gz

#驱动拷贝
cp mysql-connector-j-8.0.31/mysql-connector-j-8.0.31.jar ./apache-dolphinscheduler-3.1.4-bin/api-server/libs/
cp mysql-connector-j-8.0.31/mysql-connector-j-8.0.31.jar ./apache-dolphinscheduler-3.1.4-bin/alert-server/libs/
cp mysql-connector-j-8.0.31/mysql-connector-j-8.0.31.jar ./apache-dolphinscheduler-3.1.4-bin/master-server/libs/
cp mysql-connector-j-8.0.31/mysql-connector-j-8.0.31.jar ./apache-dolphinscheduler-3.1.4-bin/worker-server/libs/
cp mysql-connector-j-8.0.31/mysql-connector-j-8.0.31.jar ./apache-dolphinscheduler-3.1.4-bin/tools/libs/

#安装mysql客户端
# 修改 {mysql-endpoint} 为你mysql 连接地址
# 修改 {user} 和 {password} 为你mysql用户名和密码
mysql -h {mysql-endpoint} -u{user} -p{password}

mysql> CREATE DATABASE dolphinscheduler DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
# 修改 {user} 和 {password} 为你希望的用户名和密码
mysql> CREATE USER '{user}'@'%' IDENTIFIED BY '{password}';
mysql> GRANT ALL PRIVILEGES ON dolphinscheduler.* TO '{user}'@'%';
mysql> CREATE USER '{user}'@'localhost' IDENTIFIED BY '{password}';
mysql> GRANT ALL PRIVILEGES ON dolphinscheduler.* TO '{user}'@'localhost';
mysql> FLUSH PRIVILEGES;

# 修改 {user} 和 {password} 为你希望的用户名和密码
mysql> CREATE USER '{user}'@'%' IDENTIFIED BY '{password}';
mysql> GRANT ALL PRIVILEGES ON dolphinscheduler.* TO '{user}'@'%';
mysql> CREATE USER '{user}'@'localhost' IDENTIFIED BY '{password}';
mysql> GRANT ALL PRIVILEGES ON dolphinscheduler.* TO '{user}'@'localhost';
mysql> FLUSH PRIVILEGES;
```

```bash
vi bin/env/dolphinscheduler_env.sh
```
修改数据库配置
```bash
# Database related configuration, set database type, username and password
# 修改 {mysql-endpoint} 为你mysql 连接地址
# 修改 {user} 和 {password} 为你mysql用户名和密码
export DATABASE=${DATABASE:-mysql}
export SPRING_PROFILES_ACTIVE=${DATABASE}
export SPRING_DATASOURCE_URL="jdbc:mysql://{rds-endpoint}/dolphinscheduler?useUnicode=true&characterEncoding=UTF-8&useSSL=false"
export SPRING_DATASOURCE_USERNAME={user}
export SPRING_DATASOURCE_PASSWORD={password}
```

执行数据初始化
```bash
bash apache-dolphinscheduler/tools/bin/upgrade-schema.sh
```

**11、修改`install_env.sh`**

```bash
cd /usr/local/src/apache-dolphinscheduler
vi bin/env/install_env.sh 
```

```bash
# 替换IP为DolphinScheduler 所部署EC2私有IP地址
ips=${ips:-"10.100.1.220"}
masters=${masters:-"10.100.1.220"}
workers=${workers:-"10.100.1.220:default"}
alertServer=${alertServer:-"10.100.1.220"}
apiServers=${apiServers:-"10.100.1.220"}
installPath=${installPath:-"~/dolphinscheduler"}
```

**12、修改`dolphinscheduler_env.sh`**

```bash
cd /usr/local/src/
mv apache-dolphinscheduler-3.1.4-bin apache-dolphinscheduler
cd ./apache-dolphinscheduler
vi bin/env/dolphinscheduler_env.sh
```
修改dolphinscheduler环境变量
```bash
export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/jre-1.8.0-openjdk-1.8.0.362.b08-1.amzn2.0.1.x86_64}
export PYTHON_HOME=${PYTHON_HOME:-/bin/python}
```

**13、启动**

```bash
cd /usr/local/src/apache-dolphinscheduler
su dolphinscheduler
bash ./bin/install.sh
```

**14、url访问**
使用IP为DolphinScheduler 所部署EC2公有IP地址
[http://ec2-endpoint:12345/dolphinscheduler/ui/login](http://54.250.246.138:12345/dolphinscheduler/ui/login)

初始用户名/密码 **admin/dolphinscheduler123**

至此，DolphinScheduler部署工作完成
