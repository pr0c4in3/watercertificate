import io
import mimetypes

from werkzeug.utils import secure_filename
from watermark_embed import watermark_embed
from watermaek_extract import watermark_extract
import os
import random

white_list = {'png', 'jpg', 'bmp', 'jpeg'}


class web:
    def __init__(self):
        self.watermark_extract = None
        self.watermark_embed = None
        self.mimetype = None
        self.extension = None
        self.wm_text = None
        self.filename_in: str = None
        self.filename_out: str = None
        self.path_in: str = None
        self.path_out: str = None
        self.password: int = 0
        self.path: str = None

    def creat_path(self):
        self.path: str = 'image/' + str(random.randint(1, 99999)) + '/'
        os.mkdir(self.path)
        self.path_in = self.path + 'input/'
        self.path_out = self.path + 'output/'
        os.mkdir(self.path_in)
        os.mkdir(self.path_out)

    def unpack(self, result, file):
        self.password = result['password_img']
        self.wm_text = result['wm_text']
        self.watermark_embed = watermark_embed(password_img=self.password)
        self.watermark_extract = watermark_extract(password_img=self.password)
        self.creat_path()
        file.save(self.path_in + self.filename_in)

    # 删除由用户上传文件产生的文件和文件夹
    def delete(self):
        os.remove(self.path_in + self.filename_in)
        os.remove(self.path_out + self.filename_out)
        os.rmdir(self.path_in)
        os.rmdir(self.path_out)
        os.rmdir(self.path)

        # 将输出文件导入内存中

    def read_filename_to_memory(self):
        file_path = self.path_out + self.filename_out
        self.mimetype, _ = mimetypes.guess_type(file_path)
        return_data = io.BytesIO()
        with open(file_path, 'rb') as fo:
            return_data.write(fo.read())
        return_data.seek(0)
        return return_data

    def verify(self, file, result):
        self.filename_in = secure_filename(file.filename)
        name_and_extension = self.filename_in.split('.')
        self.extension = name_and_extension[-1]
        if self.extension.lower() in white_list:
            self.unpack(result, file)
            return True
        else:
            return False

    def embed(self):
        self.watermark_embed.embe(filename=self.filename_in, password_img=self.password, mode='str',
                                  wm_content=self.wm_text, filename_out_extension=self.extension,
                                  path_in=self.path_in, path_out=self.path_out)
        self.filename_out = str(len(self.watermark_embed.wm_bit)) + '.' + self.extension
        return_data = self.read_filename_to_memory()
        self.delete()
        return return_data

    def extract(self):
        wm = self.watermark_extract.extract(filename=self.filename_in, embed_img=None, wm_shape=self.wm_text,
                                            out_wm_name=None, mode='str')
        return wm



