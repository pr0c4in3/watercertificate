import numpy as np
import cv2


def normalized_correlation(image, watermark):
    # 计算原始图像和数字水印的平均值和标准差
    mean_image = np.mean(image)
    std_image = np.std(image)
    mean_watermark = np.mean(watermark)
    std_watermark = np.std(watermark)

    # 计算归一化相关系数
    n = image.shape[0] * image.shape[1]
    nc = np.sum((watermark - mean_watermark) * (image - mean_image)) / (n * std_watermark * std_image)

    return nc

# 加载原始图像和数字水印
image = cv2.imread("image.jpg", cv2.IMREAD_GRAYSCALE)
watermark = cv2.imread("watermark.jpg", cv2.IMREAD_GRAYSCALE)

# 调用归一化相关系数函数
nc = normalized_correlation(image, watermark)

# 打印计算得到的归一化相关系数
print("Normalized Correlation: ", nc)
