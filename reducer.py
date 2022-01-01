import date_string as ds

data_path = 'data.txt'
result_path = 'result.txt'

def main():
    results = {}
    users = {}
    rank = {}
    with open(data_path, 'r') as f:
        data = f.readlines()
        for line in data:
            line = line.strip('\n').strip(']').strip('[')
            line = line.split(',')
            key = line[0].strip('\'')
            username = line[1].strip(' ').strip('\'')
            date,action = key.split('_')
            date = ds.DateString(date)
            if(date.today()- date <= 30):
                if action in results.keys():
                    results[action] += 1
                else:
                    results[action] = 1
                # print(users)
                if username in users.keys():
                    rank[username] += 1
                    if action in users[username].keys():
                        users[username][action] += 1
                    else:
                        users[username][action] = 1
                else:
                    users[username] = {}
                    users[username][action] = 1
                    rank[username] = 1
        f.close()
    with open(result_path, 'w') as f:
        print('30天之内每种访问操作的总数量如下：')
        f.write('30天之内每种访问操作的总数量如下：\n')
        for item in results.items():
            print(item)
            f.write(str(item)+'\n')
        print('---------------------')
        f.write('---------------------\n')
        rank = sorted(rank.items(), key = lambda kv:(kv[1], kv[0]), reverse=True)
        cnt = 0
        print('30天用户操作总数排行前十的有：')
        f.write('30天用户操作总数排行前十的有：\n')
        for name in rank:
            cnt += 1
            print(f'排名第{cnt}, 用户{name[0]}, 总操作数 {name[1]}, 包括以下：')
            print(users[name[0]])
            f.write(f'排名第{cnt}, 用户{name[0]}, 总操作数 {name[1]}, 包括以下：\n')
            f.write(str(users[name[0]])+'\n')
            if(cnt >= 10):
                break
        f.close()

if __name__ == "__main__":
    main()
