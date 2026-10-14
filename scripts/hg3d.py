"""CLI: python scripts/hg3d.py check|job|report [paths]."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hgcloud.core import load,save_report
from hgcloud.jobs import create_job
from hgcloud.preview import build_html

def main():
    p=argparse.ArgumentParser(description='HG 3D CLOUD AI - quản lý scene / kiểm định thông số')
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('check'); a.add_argument('input'); a.add_argument('--out',default='outputs/qa_report.json')
    b=sub.add_parser('job'); b.add_argument('input'); b.add_argument('--jobs-root',default='jobs')
    c=sub.add_parser('report'); c.add_argument('json'); c.add_argument('--out',default='outputs/qa_report.html')
    args=p.parse_args()
    if args.cmd=='check':
        print(save_report(load(args.input),args.out)['status']); print('Báo cáo:',args.out)
    elif args.cmd=='job': print('Tạo job:',create_job(args.input,args.jobs_root))
    else: print('Đã tạo:',build_html(args.json,args.out))
if __name__=='__main__':main()
