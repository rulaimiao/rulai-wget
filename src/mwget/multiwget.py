import os
import time
import shutil
import hashlib
from urllib import parse, request, error
from multiprocessing import Pool



class FileMwget():


    def __init__(self, url, save_path=None, debug=False ,*args, **kwargs):
        self.url = url
        self.debug = debug
        if not save_path:
            save_path = url.split('/')[-1]
        if not os.path.isabs(save_path):
            save_path = os.path.join(os.getcwd(), save_path)
        self.save_path = save_path
        self.hash = self.md5(url)
        self.tmp_dir = os.path.join(os.getcwd(), 'tmp')
        self.data_path = os.path.join(self.tmp_dir, self.hash)
        self.start_time = time.time()
        self.meta = {}
        self.retry_times = 3
        self.referer = None
        self.complicate_num = 100
        self.chunk_size = 256
        self.cookie = None
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
            'Connection': 'keep-alive',
            'DNT': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.45 Safari/537.36'
        }

        if "retry_times" in kwargs:
            self.retry_times = int(kwargs["retry_times"])
        if "referer" in kwargs:
            self.referer = kwargs['referer']
            self.headers['Referer'] = self.referer
        if "complicate_num" in kwargs:
            self.complicate_num = int(kwargs['complicate_num'])
        if "chunk_size" in kwargs:
            self.chunk_size = int(kwargs['chunk_size'])
        return super().__init__(*args, **kwargs)


    def md5(self, string):
        m = hashlib.md5()
        m.update(string.encode())
        md5_string = m.hexdigest()
        return md5_string


    def logging_msg(self, *args):
        if self.debug:
            print(" ".join([str(a) for a in args]))


    def init(self):
        if not os.path.exists(self.tmp_dir) and not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)
        if not os.path.exists(self.data_path) and not os.path.isdir(self.data_path):
            os.mkdir(self.data_path)

        size = self.get_source_size()
        if size and size < 0:
            raise Exception("不能获取到文件长度 {}".format(self.url))
        self.meta['size'] = size
        self.meta['size_readable'] = self.readable_size(size)
        self.meta['num'] = 1
        if size > 1024 * self.chunk_size:
            self.meta['num'] = int(size / 1024 / self.chunk_size)
        print(self.meta)
        self.meta['chunk_size'] = int(size / self.meta['num'])
        

    def readable_size(self, size_readable, count=0):
        
        unit_list = ['B', 'KB', 'MB', 'GB', 'TB']
        if count+1 == len(unit_list) or size_readable < 1024:
            get_size_unit = lambda count : unit_list[count] if count < len(unit_list)-1 else unit_list[-1]
            return "{:.2f} {}" .format(size_readable, get_size_unit(count))
        size_readable = size_readable / 1024 
        count +=1 
        return self.readable_size(size_readable, count=count)
        

    def get_source_size(self):
        for i in range(0, self.retry_times):
            try:
                return self.get_url_length()
            except:
                self.logging_msg("不能获取到文件大小,重试:{}".format(i))
        else:
            raise Exception("获取大小失败, url : {} ; retry : {}".format())


    def get_url_length(self):
        url_request = self.make_a_request()
        url_request.get_method = lambda: 'HEAD'
        try:
            url_response = request.urlopen(url_request)
            content_length  = url_response.getheader(name="Content-Length")
            if content_length:
                return int(content_length)
        except error.URLError as e:
            self.logging_msg(e)
        return -1


    def make_a_request(self):
        o = parse.urlparse(self.url)
        self.headers['Host'] = o.netloc
        if self.referer:
            self.headers['Referer'] = self.referer
        if self.cookie:
            self.headers['Cookie'] = self.cookie
        
        return request.Request(self.url, headers=self.headers)


    def download(self, start, end):

        url_reqest = self.make_a_request()
            
        url_reqest.headers['Range'] = 'bytes={}-{}'.format(start, end)
        page = request.urlopen(url_reqest)
        return page.read()

            

    def download_chunk(self, start, end):
        
        
        for i in range(0, self.retry_times):
        
            try:
                return self.download(start, end)
            except:
                
                self.logging_msg("can't download {}-{}, try {}".format(start, end, i))
        
        time.sleep(10)
        raise Exception("can't download {}-{}, retry {}".format(start, end, self.retry_times))

    def worker(self, index):
        ck_path = self.chunk_path(index)
        if os.path.exists(ck_path):
            return self.logging_msg(ck_path, "exist")
        _start, _end = self.chunk_range(index)
        data = self.download_chunk(_start, _end)
        if not data:
            return self.logging_msg(ck_path, "get data failed")
        with open(ck_path, "wb") as f:
            f.write(data)
        self.logging_msg(self.get_dirs())

    def run(self):
        self.init()
        self.logging_msg("meta info", self.meta)
        
        if self.meta['num'] < self.complicate_num:
            self.complicate_num = self.meta['num']
        task_list = []
        pool = Pool(processes=self.complicate_num)

        for i in range(0, self.meta['num']):
            pool.apply_async(self.worker, (i,))
        
        
        pool.close()
        pool.join()
        
        print(self.is_finished())

        self.combine()
        self.clean()
        print(self.get_report())

    def get_dirs(self):
        chunks = [f for f in os.listdir(self.data_path) if '-' in f]
        return len(chunks) * 1.0 / self.meta['num']

    def is_finished(self):
        if self.get_dirs() == 1:
            return True
        return False
    
    def combine(self):
        if not self.is_finished():
            raise Exception("not finished download")
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time
        with open(self.save_path, 'ab') as f:
            for i in range(0, self.meta['num']):
                ck_path = self.chunk_path(i)
                with open(ck_path, 'rb') as ck_file:
                    f.write(ck_file.read())
            self.logging_msg("all donw ! elapsed time {:.3f}".format(self.elapsed_time))


    def clean(self):
        if os.path.exists(self.data_path) and os.path.isdir(self.data_path):
            shutil.rmtree(self.data_path)
        
        if not os.listdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)


    def chunk_path(self, index):
        _start, _end = self.chunk_range(index)
        return os.path.join(self.data_path, "{}-{}".format(_start, _end))

    
    def chunk_range(self, index):
        _start = index * self.meta['chunk_size']
        _end = _start + self.meta['chunk_size'] - 1
        if index is self.meta['num'] - 1:
            _end += self.meta['size'] % self.meta['num']
        return _start, _end


    def get_report(self):
        return {
            "size": self.meta['size'],
            "size_readable": self.meta['size_readable'],
            "num": self.meta['num'],
            "start_time": self.start_time,
            "end_time" : self.end_time,
            "elapsed_time": self.elapsed_time,
            "speed": '{}/s'.format(self.readable_size(self.meta['size']/self.elapsed_time))
        }


if __name__ == "__main__":
    url =""
    g = FileMwget(url, debug=True, save_path="123123.mp4")
    g.run()
    