import copy
import sys
import numpy as np
import cv2
from pywt import dwt2, idwt2
from cv2 import dct, idct
from numpy.linalg import svd


class watermark_embed:
    def __init__(self, password_img):
        self.idx_shuffle = None
        self.img = None  # 原图
        self.img_yuv = None  # 图片的yuv格式
        self.alpha = None  # 图片的透明层
        self.wm = None  # 水印
        self.block_shape = np.array([4, 4])  # 低频部分的子块的形状
        self.ca = [np.array([])] * 3  # 储存低频部分
        self.hvd = [np.array([])] * 3  # 储存高频部分
        self.ca_block = [np.array([])] * 3  # 储存低频四维分块后的结果
        self.wm_bit = None  # 储存水印的bit
        self.wm_size = 0  # 水印大小
        self.block_num = 0  # 原图片可插入的个数
        self.part_shape = None
        self.password_img = password_img
        self.ca_part = [np.array([])] * 3
        self.d1 = 36

    def read_img(self, filename=None, path_in: str = None):
        self.img = cv2.imread(
            filename=path_in + filename, flags=cv2.IMREAD_UNCHANGED)  # 读取图片
        if self.img.shape[2] == 4:
            if self.img[:, :, 3].min() < 255:
                self.alpha = self.img[:, :, 3]  # 提取照片的alpha通道并赋给alpha
                self.img = self.img[:, :, :3]  # 将照片的alpha通道删除

        self.img = self.img.astype(np.float32)
        self.img_shape = self.img.shape[:2]

        self.img_yuv = cv2.copyMakeBorder(cv2.cvtColor(self.img, cv2.COLOR_BGR2YUV), 0, self.img_shape[0] % 2, 0,
                                          self.img_shape[1] % 2, cv2.BORDER_CONSTANT,
                                          value=(0, 0, 0))  # 将原图转化为yuv格式，并将其行和列都用黑色填补成偶数
        # 计算dwt变换后的低频子带的形状
        self.ca_shape = [(i + 1) // 2 for i in self.img_shape]

        self.ca_block_shape = (
            self.ca_shape[0] // self.block_shape[0], self.ca_shape[1] // self.block_shape[1], self.block_shape[0],
            self.block_shape[1])  # 计算低频子带分解后的形状
        strides = 4 * np.array([self.ca_shape[1] * self.block_shape[0],
                                self.block_shape[1], self.ca_shape[1], 1])
        # 计算步长
        # self.ca_shape[1] * self.block_shape[0]表示每个子块的字节数
        # block_shape[1] 表示每行需要跨越的字节数
        # ca_shape[1]代表列数
        # 1 代表每次跳过一个字节
        # 由于每个元素占用4个字节，所以最终*4
        # 参考https://zhuanlan.zhihu.com/p/597292224
        for channel in range(3):
            self.ca[channel], self.hvd[channel] = dwt2(
                self.img_yuv[:, :, channel], 'haar')  # 利用dwt变换将图片的高频部分和低频部分分离
            self.ca_block[channel] = np.lib.stride_tricks.as_strided(self.ca[channel].astype(np.float32),
                                                                     self.ca_block_shape, strides)
            # 将原图的低频部分分块

    def read_wm(self, wm_content, mode='str'):
        if mode == 'img':
            wm = cv2.imread(filename=wm_content, flags=cv2.IMREAD_GRAYSCALE)

            self.wm_bit = wm.flatten() > 128
        elif mode == 'str':
            byte = bin(int(wm_content.encode('utf-8').hex(), base=16))[2:]
            self.wm_bit = (np.array(list(byte)) == '1')
        else:
            self.wm_bit = np.array(wm_content)

        self.wm_size = self.wm_bit.size

        np.random.RandomState(int(self.password_img)).shuffle(self.wm_bit)
        self.wm_size = self.wm_bit.size

    def init_block_index(self):
        self.block_num = self.ca_block_shape[0] * self.ca_block_shape[1]
        if self.wm_size > self.block_num:
            print("水印太大")
            sys.exit()
        self.part_shape = self.ca_block_shape[:2] * self.block_shape
        self.block_index = [(i, j) for i in range(self.ca_block_shape[0])
                            for j in range(self.ca_block_shape[1])]

    def block_add_wm(self, arg1, arg2, arg3):
        block, shufflere, i = arg1, arg2, arg3
        wm_1 = self.wm_bit[i % self.wm_size]

        u, s, v = svd(dct(block))
        s[0] = (s[0] // self.d1 + 1 / 4 + 1 / 2 * wm_1) * self.d1
        return idct(np.dot(u, np.dot(np.diag(s), v)))

    def embed(self, filename=None, path_out: str = None):  # 嵌入加输出
        self.init_block_index()

        embed_ca = copy.deepcopy(self.ca)
        embed_yuv = [np.array([])] * 3

        self.idx_shuffle = random_strategy1(self.password_img, self.block_num,
                                            self.block_shape[0] * self.block_shape[1])

        for channel in range(3):

            tmp = [self.block_add_wm(self.ca_block[channel][self.block_index[i]], self.idx_shuffle[i], i)
                   for i in range(self.block_num)]
            for i in range(self.block_num):
                self.ca_block[channel][self.block_index[i]] = tmp[i]

            self.ca_part[channel] = np.concatenate(
                np.concatenate(self.ca_block[channel], 1), 1)

            embed_ca[channel][:self.part_shape[0],
            :self.part_shape[1]] = self.ca_part[channel]
            embed_yuv[channel] = idwt2(
                (embed_ca[channel], self.hvd[channel]), "haar")
        embed_img_yuv = np.stack(embed_yuv, axis=2)

        embed_img_yuv = embed_img_yuv[:self.img_shape[0], :self.img_shape[1]]
        embed_img = cv2.cvtColor(embed_img_yuv, cv2.COLOR_YUV2BGR)
        embed_img = np.clip(embed_img, a_min=0, a_max=255)
        if self.alpha is not None:
            embed_img = cv2.merge([embed_img.astype(np.uint8), self.alpha])

        cv2.imwrite(filename=path_out+ filename, img=embed_img)

    def embe(self, filename: str, password_img: int, mode: str, wm_content: str, filename_out_extension: str, path_in: str,path_out:str):  # 嵌入
        self.password_img = password_img
        self.read_img(filename=filename, path_in=path_in)  # 读取照片
        self.read_wm(wm_content=wm_content, mode=mode)  # 读取水印
        self.embed(filename=str(len(self.wm_bit)) + '.' + filename_out_extension, path_out=path_out)  # 嵌入


def random_strategy1(seed, size, block_shape):
    return np.random.RandomState(int(seed)) \
        .random(size=(size, block_shape)) \
        .argsort(axis=1)
