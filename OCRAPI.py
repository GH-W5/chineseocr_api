# -*- coding:UTF-8 -*-

# @author  : admin
# @file    : OCRAPI.py
# @datetime: 2022/8/16 15:40
# @software: PyCharm

"""
文件说明：
    
"""
import os
import sys
import time
import json
import logging
from PIL import Image

from model import OcrHandle
from backend.tools import log
from config import dbnet_max_size
from backend.tools.np_encoder import NpEncoder

logger = logging.getLogger(log.LOGGER_ROOT_NAME + '.' + __name__)

ocrhandle = OcrHandle()


class OCRRun:
    def __init__(self, img_path, output_path):
        self.img_path = img_path
        self.output_path = output_path
        # 创建保存文件路径
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        log_info = {
            'code': 200,
            'img_path': img_path,
            'output_path': output_path,
        }
        logger.info(json.dumps(log_info, cls=NpEncoder))

        if not os.path.exists(self.img_path):
            error_log = {
                'code': 400, 'msg': f'{self.img_path}文件不存在',
            }
            logger.error(error_log, exc_info=True)
            raise Exception(f'{self.img_path}文件不存在')

    def run(self):
        start_time = time.time()
        img = Image.open(self.img_path)
        img_w, img_h = img.size
        short_size = round(max(img_w, img_h) / 32 + 0.5) * 32
        res = []
        do_det = True
        if short_size < 64:
            res.append("短边尺寸过小，请调整短边尺寸")
            do_det = False

        short_size = 32 * (short_size // 32)

        if max(img_w, img_h) * (short_size * 1.0 / min(img_w, img_h)) > dbnet_max_size:
            res.append("图片resize后长边过长，请调整短边尺寸")
            do_det = False

        if do_det:
            res = ocrhandle.text_predict(img, short_size)
        # 结果写入指定文件
        res = [{"pos": rect.tolist(), "value": txt.split('、')[-1].strip(), "weight": float(confidence)} for
               rect, txt, confidence in res]
        res_dic = {"result": res}
        json_str = json.dumps(res_dic, indent=4, ensure_ascii=False)
        with open(self.output_path, 'w', encoding='utf-8') as json_file:
            json_file.write(json_str)

        log_info = {
            'code': 200,
            'return': res,
            'speed_time': round(time.time() - start_time, 2)
        }
        logger.info(json.dumps(log_info, cls=NpEncoder, ensure_ascii=False))
        return 0


def ocr_run(file_name, arg1, arg2=None):
    """

    :param file_name: 文件名，无用
    :param arg1: 图片路径
    :param arg2: json保存路径
    :return:
    """
    filepath, filename = os.path.split(arg1)
    fname, ext = os.path.splitext(filename)
    if not arg2:
        arg2 = os.path.join(filepath, fname + '.json')
    OCRRun(arg1, arg2).run()
    return arg2


if __name__ == '__main__':
    # img_path = 'C:/Users/admin/Desktop/orc_test.jpg'
    # print(sys.argv)

    ocr_run(*sys.argv)

