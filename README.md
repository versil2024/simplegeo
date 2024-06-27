# simplegeo

nginxで国ごとのアクセス制限をかけるためのツールです。
GeoIのgeoディレクティブPを使わずで、アクセス制限できるよう、geoディレクティブ用のファイルを生成します。

## 動作環境
- Python 3
- 必要パッケージ: yaml, request

## インストール

次の二つのファイルを同じディレクトリに保存してください。
- symplegeo.py
- country_code.yaml

symplegeo.pyに実行権を付与します。
```sh
chmod a+x symplegeo.py
```

## 動作概要

コマンドを実行すると、次の処理を行います。
1. confファイル保存用のディレクトリにAPNICのデータをダウンロード（ディレクトリがなければ作成）
2. ダウンロードしたデータから、nginxのgeoディレクティブで使える形で、国別のconfファイルを生成

## コマンドオプション

`-h`オプションをつけて実行すると、次のようにヘルプが表示されます。

```
Simple geo file generator for nginx

options:
  -h, --help         show this help message and exit
  -n, --no_download  Do not download data before generating conf files
  -v, --verbose      Show downloading status
  --savedir SAVEDIR  The path to store conf files
  --dataurl DATAURL  URL of APNIC data
```

- `-n`, `--no_download` : confファイル生成の前に、ダウンロードをしません。
- `-v`, `--verbose` : APNICからのダウンロード時に状況表示をします。
- `--savedir` : confファイルの保存場所を指定します。デフォルトは`/usr/local/etc/nginx/geoconf`です。
- `--dataurl` : APNICのデータをダウンロードするURLを指定します。デフォルトは`https://ftp.apnic.net/stats/apnic/delegated-apnic-latest`です。


## 使い方

### confファイル作成
上記手順に従ってインストールし、スクリプトを実行すると`/usr/local/etc/nginx/geoconf`の下に国コード別にconfファイルが作成されます。

作成されるファイル名は、2文字の国コードの後ろに拡張子`.conf`がついたものです。

国コードがどの国のものかわからない場合には、confファイルを開けば確認できます。confファイルには1行目にコメントとして、国名が日本語で記載してあります。

または`country_code.yaml`を開けば、国コードのアルファベット順に国名との対応が記載されているので、参照してください。ただし、`country_code.yaml`に記載されている国すべてにIPアドレスが割り当てられているわけではありません。あくまで国コードから国名を参照するための参考用にどうぞ。

### 自動更新設定
cron登録すれば、confファイルを自動的に更新できます。
```crontab
20 15 * * * /usr/local/bin/simplegeo.py
```

### nginx.conf編集
`nginx.conf`を編集し、`http`ディレクティブ内に`geo`ディレクティブを定義し、この中で生成した国コードのconfファイルを読み込ませます。  


`include geoconf/*.conf;`とすれば1行で済みますが、使わない定義まですべて読み込んでしまうとメモリを無駄に消費するので、必要なファイルだけ読み込むのがお薦めです。

```Nginx
http {
    :
    :
    geo $country_code {
        default ZZ;
        proxy 11.22.33.44; #リバースプロキシ使用時

        # 使用するconfファイルをinclude
        include geoconf/JP.conf;
        include geoconf/US.conf;
        include geoconf/CN.conf;
        include geoconf/RU.conf;
    }
    :
    :
}
```
次に、同じく`http`ディレクティブ内に`map`ディレクティブを使ってアクセス制限の定義を作成します。

1番目の引数に`geo`ディレクティブで定義した変数名を使用する以外、GeoIPモジュールを使うときと指定方法は変わりません。アクセス制限の定義は、2番目に定義する変数名を変えれば複数定義可能です。

```Nginx
http {
    :
    :
    map $country_code $allowed_remote {
        # 許可した国以外は拒否する場合
        default no;
        JP yes;
    }

    map $country_code $denied_remote {
        # 拒否する国以外は許可する場合
        default yes;
        US no;
        CN no;
        RU no;
    }
    :
    :
}
```
実際のアクセス制限は、`server`ディレクティブ、または`location`ディレクティブ内に、次のように記述して行います。
```Nginx
http {
    :
    :
    location / {
        if ($denied_remote = no) {
            return 403;
        }
    }

    location /restricted {
        if ($allowed_remote = no) {
            return 403
        }
    }
    :
    :
}
```