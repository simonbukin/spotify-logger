import redis

from auth import redis_host

def redis_connect(host, db_num):
    r = redis.StrictRedis(host=host, db=db_num)
    return r

r = redis_connect(redis_host, 0)

print(r.dbsize())

# for key in r.scan_iter('activity:*'):
#     print(r.hgetall(key))
