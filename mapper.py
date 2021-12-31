import sys
import date_string as ds
log_path = 'log.txt'
data_path = 'data.txt'

def main():
    list = []
    with open(log_path, 'r') as f:
        data = f.readlines()
        for line in data:
            line = line.strip('\n')
            date,username,action,dist = line.split(' ')
            list.append([date+'_'+action,username])
        f.close()
    with open(data_path, 'w') as f:
        for line in list:
            f.write(str(line)+'\n')
        f.close()

if __name__ == "__main__":
    main()