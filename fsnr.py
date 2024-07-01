import cv2 as cv
import math
import numpy as np
 
 
def psnr1(img1, img2):
    # compute mse
    # mse = np.mean((img1-img2)**2)
    mse = np.mean((img1 / 1.0 - img2 / 1.0) ** 2)
    # compute psnr
    if mse < 1e-10:
        return 100
    psnr1 = 20 * math.log10(255 / math.sqrt(mse))
    return psnr1
 
 
def psnr2(img1, img2):#第二种法：归一化
    mse = np.mean((img1 / 255.0 - img2 / 255.0) ** 2)
    if mse < 1e-10:
        return 100
    PIXEL_MAX = 1
    psnr2 = 20 * math.log10(PIXEL_MAX / math.sqrt(mse))
    return psnr2
 
 
imag1 = cv.imread("luna.png") #原图
print(imag1.shape)
imag2 = cv.imread("123.png")    #水印图
print(imag2.shape)
#如果大小不同可以强制改变
# imag2 = imag2.reshape(352,352,3)
#print(imag2.shape)
res1 = psnr1(imag1, imag2)
print("res1:", res1)
res2 = psnr2(imag1, imag2)
print("res2:", res2)
 