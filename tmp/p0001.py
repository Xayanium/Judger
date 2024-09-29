# -*- coding: utf-8 -*-
# @Time    : 2024/9/15 14:48
# @Author  : Xayanium

def add(a, b):
    return a + b


if __name__ == '__main__':
    a, b = map(int, input().split())
    print(add(a, b))

