import copy
import sys
import numpy as np
import cv2
from pywt import dwt2, idwt2
from cv2 import dct, idct
from numpy.linalg import svd


class watermark_extract:
    def __init__(self, password_img):
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

    def read_img_arr(self, img):
        # 处理透明图 (即将图片的alpha通道和rgb通道分离)
        self.alpha = None
        if img.shape[2] == 4:  # img.shape表示img的第三个（数组从0开始）维度（表示通道数）是否为4，若为4，即有透明度该参数
            # img.shape的数组表示图片的参数信息，[0]代表高度，即行数，[1]代表宽度，即列数，[3]代表通道数
            if img[:, :, 3].min() < 255:
                self.alpha = img[:, :, 3]  # 将照片的第四个通道（透明度）赋给alpha，该数组变为一个二维数组
                img = img[:, :, :3]  # 将照片前三个通道提取出来，即只要rgb通道

        # 读入图片->YUV化->加白边使像素变偶数->四维分块
        self.img = img.astype(np.float32)  # 将img的整数格式强转换为np.float32形
        self.img_shape = self.img.shape[:2]  # 将img的高和宽赋给img_shape

        # 如果不是偶数，那么补上白边，Y（明亮度）UV（颜色）
        self.img_YUV = cv2.copyMakeBorder(cv2.cvtColor(self.img, cv2.COLOR_BGR2YUV),
                                          0, self.img.shape[0] % 2, 0, self.img.shape[1] % 2,
                                          cv2.BORDER_CONSTANT, value=(0, 0, 0))

        # cv2.cvtColor(self.img, cv2.COLOR_BGR2YUV) 将img图像由rgb格式转化为yuv格式
        # 补充像素，将其高和宽转化为偶数
        # 参数分别对应 上，下，左，右
        # cv2.BORDER_CONSTANT 参数表明补充的像素不会改变
        # value=(0,0,0)表示黑色

        self.ca_shape = [(i + 1) // 2 for i in self.img_shape]
        # //代表整除    对于img.shape这个数组，（每项+1）/2，并向下取整
        # 计算dwt变换后的低频数组的形状，即每个维度的原来的一半

        self.ca_block_shape = (self.ca_shape[0] // self.block_shape[0], self.ca_shape[1] // self.block_shape[1],
                               self.block_shape[0], self.block_shape[1])
        # ca_shape(低频子带) 计算其分成4*4的形状(计算一共有多少行的子块，和多少列的子块)
        strides = 4 * np.array([self.ca_shape[1] * self.block_shape[0],
                                self.block_shape[1], self.ca_shape[1], 1])
        # 计算步长，计算ca_shape分解时应该从每个块的开始部分跳过多少字节到达下一个子块
        # self.ca_shape[1] * self.block_shape[0]表示每个子块的字节数
        # block_shape[1] 表示每行需要跨越的字节数
        # ca_shape[1]代表列数
        # 1 代表每次跳过一个字节
        # 由于每个元素占用4个字节，所以最终*4

        for channel in range(3):
            self.ca[channel], self.hvd[channel] = dwt2(
                self.img_YUV[:, :, channel], 'haar')
            # 对于上述yuv格式的图片的每个通道进行dwt（小波变换）
            # ca[channel]接受变换后的低频部分 主要包含图像的大致轮廓和较低的细节信息
            # hvd[channel]接受变换后的高频部分 主要包含细节分量

            # 转为4维度
            self.ca_block[channel] = np.lib.stride_tricks.as_strided(self.ca[channel].astype(np.float32),
                                                                     self.ca_block_shape, strides)
            # np.lib.stride_tricks.as_strided高效分块
            # 对于原始的低频分量进行切块
            # ca[channel].astype[np.float32]将数据强转化为float32格式
            # ca_block_shape表示每个子块的形状，strides表示步长
            # 根据给定的子块形状和步长分割经过dwt变换过的矩阵
            # 对于步长的理解可以参考https://zhuanlan.zhihu.com/p/597292224

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
        if (self.wm_size > self.block_num):
            print("水印太大")
            sys.exit()
        self.part_shape = self.ca_block_shape[:2] * self.block_shape
        self.block_index = [(i, j) for i in range(self.ca_block_shape[0])
                            for j in range(self.ca_block_shape[1])]

    def block_get_wm(self, arg1, arg2):
        block, shuffler = arg1, arg2

        u, s, v = svd(block)
        wm = (s[0] % self.d1 > self.d1 / 2) * 1
        return wm

    def extract_raw(self, img):
        self.read_img_arr(img=img)
        self.init_block_index()

        wm_blcok_bit = np.zeros(shape=(3, self.block_num))

        self.idx_shuffle = random_strategy1(seed=self.password_img, size=self.block_num,
                                            block_shape=self.block_shape[0])
        for channel in range(3):
            wm_blcok_bit[channel, :] = [
                self.block_get_wm(self.ca_block[channel][self.block_index[i]], self.idx_shuffle[i]) for i in
                range(self.block_num)]

        return wm_blcok_bit

    def extract_avg(self, wm_block_bit):
        wm_avg = np.zeros(shape=self.wm_size)
        for i in range(self.wm_size):
            wm_avg[i] = wm_block_bit[:, i::self.wm_size].mean()
        return wm_avg

    def extract1(self, img, wm_shape):
        self.wm_size = np.array(wm_shape).prod()
        wm_block_bit = self.extract_raw(img=img)
        wm_avg = self.extract_avg(wm_block_bit)
        return wm_avg

    def extract_with_kmeans(self, img, wm_shape):
        wm_avg = self.extract1(img=img, wm_shape=wm_shape)
        return one_dim_kmeans(wm_avg)

    def extract_decrypt(self, wm_avg):
        wm_index = np.arange(self.wm_size)
        np.random.RandomState(int(self.password_img)).shuffle(wm_index)
        wm_avg[wm_index] = wm_avg.copy()
        return wm_avg

    def extract(self, filename: str, embed_img=None, wm_shape: int = 123, out_wm_name=None, mode='str') -> None:

        wm_shape=int(wm_shape)*8-1
        if filename is not None:
            embed_img = cv2.imread(filename=filename, flags=cv2.IMREAD_COLOR)

        self.wm_size = np.array(wm_shape).prod()

        wm_avg = self.extract_with_kmeans(img=embed_img, wm_shape=wm_shape)

        wm = self.extract_decrypt(wm_avg=wm_avg)

        if mode == 'img':
            wm = 255 * wm.reshape(wm_shape[0], wm_shape[1])
            cv2.imwrite(out_wm_name, wm)
        elif mode == 'str':
            byte = ''.join((np.round(wm)).astype(int).astype(str))
            wm = bytes.fromhex(hex(int(byte, base=2))[2:]).decode('utf-8', errors='replace')

        return wm


def random_strategy1(seed, size, block_shape):
    return np.random.RandomState(int(seed)) \
        .random(size=(size, block_shape)) \
        .argsort(axis=1)


def one_dim_kmeans(inputs):
    threshold = 0
    e_tol = 10 ** (-6)
    center = [inputs.min(), inputs.max()]
    for i in range(300):
        threshold = (center[0] + center[1]) / 2
        is_class01 = inputs > threshold
        center = [inputs[~is_class01].mean(), inputs[is_class01].mean()]
        if np.abs((center[0] + center[1]) / 2 - threshold) < e_tol:
            threshold = (center[0] + center[1]) / 2
            break

    is_class01 = inputs > threshold
    return is_class01

