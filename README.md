# ezVideoThumbnails

capture img from video

# pyinstaller cmd

1/ get path of openCV
import cv2
print(cv2.**file**)

> c:\Users\DT0083\AppData\Local\Programs\Python\Python310\lib\site-packages\cv2\_\_init\_\_.py
> so the path is:
> `c:\Users\DT0083\AppData\Local\Programs\Python\Python310\lib\site-packages\cv2`

2/ inclue the path when create exe file

pyinstaller main.py -n myApp --paths="`the path here`"

pyinstaller main.py -n ezThumb --onefile --paths="c:\Users\DT0083\AppData\Local\Programs\Python\Python310\lib\site-packages\cv2"
