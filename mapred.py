import mapper
import reducer

if __name__ == '__main__':
    print('-----------正在执行map操作-------------')
    mapper.main()
    print('----------正在执行reduce操作-----------')
    reducer.main()
    print('已完成! 结果可以在<result.txt>中查看')


