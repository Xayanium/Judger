# coding: utf-8
# @Author: Xayanium

def add(count: int):
    while count < 10:
        count += 1
        yield count, False


if __name__ == '__main__':
    counter = add(1)
    for out, err in counter:
        print(out)

