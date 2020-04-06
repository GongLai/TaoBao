# -*- coding: utf-8 -*-
# 模拟登录淘宝网

import json
import os
import re

import requests

s = requests.Session()
# cookies序列化文件
COOKIES_FILE_PATH = './taobao_login_cookies.txt'


class UsernameLogin:

    def __init__(self, username, ua, TPL_password_2):
        """
        账号登录对象
        :param username: 用户名
        :param ua: 加密参数
        :param TPL_password2: 加密后的密码
        """
        # 检测是否需要验证码的URL
        self.nick_check_url = 'https://login.taobao.com/member/request_nick_check.do?_input_charset=utf-8'
        # 验证淘宝用户名密码的URL
        self.verify_password_url = 'https://login.taobao.com/member/login.jhtml'
        # 访问st码的URL
        self.vst_url = 'https://login.taobao.com/member/vst.htm?st={}'
        # 淘宝个人主页URL
        self.my_taobao_url = 'https://i.taobao.com/my_taobao.htm'

        # 淘宝用户名
        self.username = username
        # 淘宝关键参数，包含用户浏览器等一些信息，很多地方会用到，从浏览器或抓包工具中复制，可重复使用
        self.ua = ua
        # 加密后的密码，从浏览器或抓包工具中复制，可重复使用
        self.TPL_password_2 = TPL_password_2
        self.headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
        }

        # 请求超时时间
        self.timeout = 3

    def _user_check(self):
        """
        检测账号是否需要验证码
        :return:
        """
        data = {
            'username': self.username,
            'ua': self.ua
        }

        try:
            resp = s.post(url=self.nick_check_url, data=data, timeout=self.timeout)
        except Exception as e:
            print('检测是否需要验证码请求失败，原因是：{}'.format(e))
            return True

        needcode = resp.json()['needcode']
        print('是否需要滑块验证：%s' % '是' if needcode else '否')
        return needcode

    def _verify_password(self):
        """
        获取st码申请地址
        :return: st码申请地址
        """
        # 登录 taobao.com 提交的数据，如果登录失败，可以从浏览器复制你的 form dara
        verify_password_data = {
            'TPL_username': self.username,
            'ncoToken': '577d470184de0ea182df2e3d450184b991b2be39',
            'slideCodeShow': 'false',
            'useMobile': 'false',
            'lang': 'zh_CN',
            'loginsite': 0,
            'newlogin': 0,
            'TPL_redirect_url': 'https://www.taobao.com/',
            'from': 'tb',
            'fc': 'default',
            'style': 'default',
            'keyLogin': 'false',
            'qrLogin': 'true',
            'newMini': 'false',
            'newMini2': 'false',
            'loginType': 3,
            'gvfdcname': 10,
            'gvfdcre': '68747470733A2F2F6C6F67696E2E74616F62616F2E636F6D2F6D656D6265722F6C6F676F75742E6A68746D6C3F73706D3D613231626F2E323031372E3735343839343433372E372E35616639313164394E467A6F373126663D746F70266F75743D7472756526726564697265637455524C3D68747470732533412532462532467777772E74616F62616F2E636F6D253246',
            'TPL_password_2': self.TPL_password_2,
            'loginASR': 1,
            'loginASRSuc': 1,
            'oslanguage': 'zh-CN',
            'sr': '1920*1080',
            'naviVer': 'chrome|80.03987149',
            'osACN': 'Mozilla',
            'osAV': '5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
            'osPF': 'Linux x86_64',
            'appkey': 00000000,
            'mobileLoginLink': 'https://login.taobao.com/member/login.jhtml?redirectURL=https://www.taobao.com/&useMobile=true',
            'um_token': 'T2D8FA904F843327ABC4614C6C33594E286CCFA21246948586EF192BDD5',
            'ua': self.ua
        }

        try:
            resp = s.post(url=self.verify_password_url, headers=self.headers, data=verify_password_data,
                          timeout=self.timeout)
            # 提取申请st码地址
            st_token_url = re.search(r'<script src="(.*?)"></script>', resp.text).group(1)
        except Exception as e:
            print(' 验证用户名和密码请求失败，原因是：{}'.format(e))
            return None
        # 提取成功则返回
        if st_token_url:
            print('验证用户名密码成功， st码申请地址：{}'.format(st_token_url))
            return st_token_url
        else:
            print('用户名密码申请失败，请更换data参数')
            return None

    def _apply_st(self):
        """
        申请st码
        :return: st码
        """
        apply_st_url = self._verify_password()
        try:
            st_resp = s.get(url=apply_st_url)
        except Exception as e:
            print('申请st码请求失败，原因：{}'.format(e))
            raise e
        st_match = re.search(r'"data":{"st":"(.*?)"}', st_resp.text)
        if st_match:
            print('获取st码成功，st码：{}'.format(st_match.group(1)))
            return st_match.group(1)
        else:
            raise RuntimeError('提取st码失败！')

    def _serialization_cookies(self):
        """
        序列化cookies
        :return:
        """
        cookies_dict = requests.utils.dict_from_cookiejar((s.cookies))
        with open(COOKIES_FILE_PATH, 'w+', encoding='utf-8') as file:
            json.dump(cookies_dict, file)

    def _deserialization_cookies(self):
        """
        反序列化cookies
        :return:
        """
        with open(COOKIES_FILE_PATH, 'r+', encoding='utf-8') as file:
            cookies_dict = json.load(file)
            cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            return cookies

    def _load_cookies(self):
        # 1. 判断cookies序列化文件是否存在
        if not os.path.exists(COOKIES_FILE_PATH):
            return False
        # 2. 加载cookies
        s.cookies = self._deserialization_cookies()
        # 3. 判断cookies是否过期
        try:
            self.get_taobao_nick_name()
        except Exception as e:
            os.remove(COOKIES_FILE_PATH)
            print('cookies过期，删除cookies文件！')
            return False
        print('加载cookies登录淘宝成功！！！')
        return True

    def login(self):
        """
        模拟登录淘宝
        :return:
        """
        # 加载cookies文件, 如果有cookies文件，使用cookies登录淘宝，反之，则使用st码登录淘宝
        if self._load_cookies():
            return True
        # 判断是否需要滑块验证码
        self._user_check()
        st = self._apply_st()
        try:
            response = s.get(url=self.vst_url.format(st), headers=self.headers)
            response.raise_for_status()
        except Exception as e:
            print('st码登录请求，原因：{}'.format(e))
            raise e
        # 登录成功，提取跳转淘宝首页链接
        my_taobao_match = re.search(r'top.location.href = "(.*?)"', response.text)
        if my_taobao_match:
            print('登录淘宝成功，跳转链接：{}'.format(my_taobao_match.group(1)))
            self._serialization_cookies()
            return True
        else:
            raise RuntimeError('登录失败！response：{}'.format(response.text))

    def get_taobao_nick_name(self):
        """
        获取淘宝昵称
        :return: 淘宝昵称
        """
        try:
            response = s.get(url=self.my_taobao_url, headers=self.headers)
            response.raise_for_status()
        except Exception as e:
            print('获取淘宝主页请求失败，原因：{}'.format(e))
            raise e
        # 提取淘宝昵称
        nick_name_match = re.search(r'<input id="mtb-nickname" type="hidden" value="(.*?)"/>', response.text)
        if nick_name_match:
            print('您的淘宝昵称是：{}'.format(nick_name_match.group(1)))
            return nick_name_match.group(1)
        else:
            raise RuntimeError('获取淘宝昵称失败！response：{}'.format(response.text))


if __name__ == '__main__':
    # 淘宝用户名
    username = '1228881058@qq.com'
    # 淘宝重要参数，从浏览器或抓包工具中复制，可重复使用
    ua = '122#de2WyJj2EEa+oEpZMEpJEJponDJE7SNEEP7rEJ+/Uft7woQLpo7iEDpWnDEeK51HpyGZp9hBuDEEJFOPpC76EJponDJL7gNpEPXZpJRgu4Ep+FQLpoGUEJLWn4yP7SQEEyuLpERdIbhBprZCnaRx9kb/Bnzg9bIKktuYrpvne+ENfs8s1mA/KLT4s0J1LzsqfBwTs6mAvmDlevUkczZGuRbJkF0uTBVsPpmC5iplk3vGmYbrUxvQclSGp/k3uztFP0eNlriEEawL8oL6JRO3w5mDrfm2DEpxn70UmebE/ZLr8o+UJDEEyB3tqWZW/IZNngL4uO8pELVZGWZRfsTbyFfDmSfbEEpMnMp1uOIEELXZ8oL6JNEERBfmqM32E5pangL4uljEDLVr8CpUJ4bEyNRDqMfjmDpxnWL18Om9E5G+08NnpzJL1DaXCqo6uqB5dbaoRMe+64+U4/b3MPaMvGvANi51ZNs1SR9s6I2QRS2b6XE9D/11ZebJ3nYaJhiZXBbpKiaBVyaiThyQ9bQTcQDzXjb3/7L3sGzET7QRg4EYp25o6I5lFGNtmgAM440H7kZ9Em2KhXlbhiAtOVHg9NOO5SGtGVW4g3yTFgwkdKasqgzjKJGgq6kn0RuaPgPp2b/VJaDVwqqkNEo1lZVmzNZ9OOY6JFgzexbXWcMdjNh+63tOLTQ/WRlHKa+50J3YvXalpuD3Iw6IWy92LhvEU+LKo2ATJ5ymOJKc5B3U9pMkNfReyN7W3cz86xzXIR5kqZVxChluOVXPm8TN9U49TtClodxIl+ohiumeNfQOeY6DZC28cpOY5Vz/94prCG91ySQh3HUSU0V8I02FR4V7YkJ33rKwW/6NrHdQ5p0jXzLQ9BomQo8hy28CkC4qOeoPX93JmuSqKQEyXCxiCZ6kPL0+GWltzexWpSeYiWLHnPwRD898Fyu5A5gXyUrxXEQOuJSRuqbH2YX1mVciaS1l5cHArO771dp6VSNhGDYZEabbCusGM27yZAx/mE7UMzY/gZ4AoI0v+BCxDDeHRZS26ZOxsT6+kwWD2v9RF8oR1dp9XWKRv1fDE0KTo8kkm4r2ZfpoJXNdYU0ikKa1GMld86fWWGWaChhtr/2xy5cHYRVBaCO+di+tEl8jjWWLU4TaLb4l5onq8LzCQV9GLAUdaUah9AmcoiJmUQaLGuczc23/udrdi67HMRnjlBI9try='
    # 加密后的密码，从浏览器或抓包工具中复制，可重复使用
    TPL_password_2 = '3390af9c04e6210559899d542a18ea16bd210ff91e31691739593c5e19d80d226fc3375e78fbca7b81bcced760458fb33931c8653ac730caefefa7c0202bb5275698f45af1ca57ff010315388d56c82cedb948626bd3d02bf757b0938582136e0322d2d9fe2ac4ad721c5fac4acb347c8e692091cd16eb521126117adc7125fd'
    login = UsernameLogin(username=username, ua=ua, TPL_password_2=TPL_password_2)
    login.login()
    login.get_taobao_nick_name()
