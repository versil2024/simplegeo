#!/usr/bin/env python3

from pathlib import Path
import argparse
import requests
import yaml

CONFDIR = '/usr/local/etc/nginx/geoconf'
APNICSRC = 'https://ftp.apnic.net/stats/apnic/delegated-apnic-latest'
COUNTRY = Path(__file__).parent / 'country_code.yaml'

def download_file(url, savedir, verbose):
    """
    指定されたパスからファイルをダウンロードして、CONFDIRに
    保存する
    """
    filepath = savedir / Path(url).name
    if verbose:
        print('Downloading data file...')
    response = requests.get(url)
    if response.status_code == 200:
        with filepath.open('wb') as f:
            f.write(response.content)
        if verbose:
            print('Download done.')
    else:
        if verbose:
            print(f'Download error: {response.status_code}')
    return filepath

def convert_ip_to_country(filename, savedir):
    """
    delegated-apnic-latestファイルからIPv4アドレスと国名を取得し、
    国別に.confファイルを作成して出力する
    """
    with COUNTRY.open('r') as f:
        country_code = yaml.safe_load(f)

    geolist = {}
    with open(filename, 'r') as f:
        for line in f:
            if '|ipv4|' in line and not 'summary' in line:
                ip_info = line.split('|')
                country = ip_info[1]
                ip_address = ip_info[3]
                tmp_cidr = int(ip_info[4])
                cidr = 32

                while tmp_cidr != 1:
                    tmp_cidr //= 2
                    cidr -= 1
                data = f'{ip_address}/{cidr} {country};'
                if not country in geolist.keys():
                    if country in country_code.keys():
                        country_jptxt = f'# {country_code[country]}'
                    else:
                        country_jptxt = '# 不明'
                    geolist[country] = [country_jptxt, data]
                else:
                    geolist[country].append(data)

    for country, list in geolist.items():
        conffile = savedir / f'{country}.conf'
        with conffile.open('w') as f:
            print(*list, sep='\n', file=f)
    return geolist

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple geo file generator for nginx')
    parser.add_argument('-n', '--no_download', action='store_true',
                        help='Do not download data before generating conf files')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show downloading status')
    parser.add_argument('--savedir', type=str, default=CONFDIR,
                        help='The path to store conf files')
    parser.add_argument('--dataurl', type=str, default=APNICSRC,
                        help='URL of APNIC data')
    
    args = parser.parse_args()
    dataurl = args.dataurl
    no_download = args.no_download
    verbose = args.verbose
    savedir = Path(args.savedir)

    # 保存用ディレクトリが存在しなければ作成
    if not savedir.exists():
        savedir.mkdir(parents=True)

    if no_download:
        filename = savedir / Path(dataurl).name
    else:
        filename = download_file(dataurl, savedir, verbose)
    convert_ip_to_country(filename, savedir)