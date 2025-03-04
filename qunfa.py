
from wcferry import Wcf
str = " 请在这里输入要群发的消息 " #群发的消息填这里
def main():
    wcf = Wcf()
    b = wcf.get_friends()
    for i in b:
        print(i['wxid'])
        wcf.send_text(str,i['wxid'])

if __name__ == '__main__':
    main()