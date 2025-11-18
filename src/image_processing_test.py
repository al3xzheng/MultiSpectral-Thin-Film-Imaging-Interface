import cv2
import numpy as np

# print(cv2.__version__)

# img = numpy.zeros((3,3), dtype=numpy.uint8)
# img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
# img.shape  inspects the structure of an image

# image = cv2.imread('MyPic.png') #imread returns a BGR image, discards transparency (alpha channel)
# imshow()
# cv2.imwrite('MyPic.jpg', image)

# The imwrite() function requires an image to be in the BGR or grayscale format with a certain number of bits per channel that the output 
# format can support. For example, bmp requires 8 bits per channel, while PNG allows either 8 or 16 bits per channel.

# An OpenCV image is a 2D or 3D array of the .array type.

# TODO build a prototype for Silas

# import cv2
# import numpy
# import os
# # Make an array of 120,000 random bytes.
# randomByteArray = bytearray(os.urandom(120000)) # numpy.random.randint(0, 256, 120000). --> reshape(300, 400)
# flatNumpyArray = numpy.array(randomByteArray)
# # Convert the array to make a 400x300 grayscale image.
# grayImage = flatNumpyArray.reshape(300, 400)
# cv2.imwrite('RandomGray.png', grayImage)
# # Convert the array to make a 400x100 color image.
# bgrImage = flatNumpyArray.reshape(100, 400, 3)
# cv2.imwrite('RandomColor.png', bgrImage)

# numpy.array is an
# extremely optimized library for these kind of operations, and because we obtain
# more readable code through NumPy's elegant methods

# print img.item(150, 120, 0) // prints the current value of B for that
# img.itemset( (150, 120, 0), 255)

image1 = cv2.imread("C:/Users/Alex/Documents/Research/URA2/Multispectral ThinFilm Imaging/data/tiger.jpg",1)
print(image1.shape)
print(image1[0, 0, 1])
image1[:,:,0] = 150
print(image1[:,:,0]) #to get BGR values [0,1,2]

image = cv2.imread("C:/Users/Alex/Documents/Research/URA2/Multispectral ThinFilm Imaging/data/White.jpg",0)
print(image.shape)
image[1:400,:] = 0
print(image)
# image[:,:,2] = 0
# print(image)
# print(image.shape())
cv2.imwrite('test.jpg', image1)
cv2.imwrite('test2.jpg', image)
# cv2.imshow(image)

# img = np.random.randint(0, 256, 120000).reshape(300, 400)
# cv2.imwrite('RandomGray.png', img)
# print(img)
# print(img.shape)
# print(img.ndim)
# # # Convert the array to make a 400x100 color image.
# bgrImage = img.reshape(100, 400, 3)
# cv2.imwrite('RandomColor.png', bgrImage)
# print(bgrImage)
# print(bgrImage.shape)

