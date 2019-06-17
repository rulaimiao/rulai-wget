import argparse
import sys
from .multiwget import FileMwget



def main(**kwargs):
    parser = argparse.ArgumentParser(
        prog='mwget',
        usage='mwget [OPTION]... URL...',
        description="这是把mwget 改为 python3 的版本, 用来做一些大文件的下载",
        add_help=False
    )

    
    parser.add_argument(
        '-V', '--version', help="输出版本", action="store_true"
    )
    parser.add_argument('URL', nargs='*', help=argparse.SUPPRESS)
    
    parser.add_argument("-d", "--debug", action="store_true", help="默认为False")

    parser.add_argument("--file_name",  help="下载后的文件名")
    
    parser.add_argument("--retry_times",  help="重试的次数")

    parser.add_argument("--complicate_num",  help="多进程的数量")

    parser.add_argument("--chunk_size",  help="分片的文件大小,默认256,随网速而定")

    parser.add_argument("--referer",  help="referer 请求的referer" )

    parser.add_argument("-h", "--help", action="store_true", help="获取帮助文档")

    parser.add_argument("-c", "--cookie", help="Cookie url")

    args = parser.parse_args()
    debug = False
    save_path = None
    if args.version:
        from .__init__ import __package_name__, __version__
        print("{} : {}".format(__package_name__, __version__))
        sys.exit()
    urls_list = []
    if args.URL:
        urls_list.extend(args.URL)

    url = urls_list[0]
    g = FileMwget(url)

    if args.debug:
        debug = True
        g.debug = debug
    if args.file_name:
        save_path=args.file_name
        g.save_path = save_path
    if args.retry_times:
        retry_times = int(args.retry_times)
        g.retry_times = retry_times
    if args.complicate_num:
        complicate_num = int(args.complicate_num)
        g.complicate_num = complicate_num
    if args.chunk_size:
        chunk_size = int(args.chunk_size)
        g.chunk_size = chunk_size
    if args.referer:
        referer = args.referer
        g.referer = referer
    if args.cookie:
        cookie = args.cookie
        g.cookie = cookie
    if args.help or not urls_list:
        parser.print_help()
        sys.exit()

    g.run()
    

if __name__ == "__main__":
    main()