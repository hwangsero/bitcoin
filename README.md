# Dillinger
## _The Last Markdown Editor, Ever_



[코인 프로젝트 개요]
- Type some Markdown on the left
- See HTML in the right
- 3개의 서버(8gb, n core)에 각 플랫폼들의 클러스터를 구성
- ✨Magic ✨


#### 파이프라인 아키텍쳐
[이미지]

#### Key Element 1. 스트리밍, 배치 코인 데이터 수집 파이프라인 구축
- 실시간 코인 거래랑 가격 정보와 최근 24시간 동안의 거래소 별 코인 데이터 수집 파이프 라인 구축
- Drag and drop images (requires your Dropbox account be linked)
- Import and save files from GitHub, Dropbox, Google Drive and One Drive

#### Key Element 2. 데이터 일관성, 정합성보다 처리량, 가용성
- 코인 별 실시간 변화량 및 추세를 보기 위함으로 일부 데이터의 유실보다 가용성과 처리성을 중심으로 설계
- 3개의 서버, 3개의 노드로 클러스터를 구성하여 가용성, 내결함성 처리
- produce ack, consistence level을 ~~로 설정함으로 인해 처리성을 중심

#### Key Element 3. 데이터 lifecycle을 자동으로 관리
- 지속적으로 쌓이는 데이터들을 관리하기 위해 데이터의 lifecycle 관리
- kafka 브로커들의 RETENTION_HOURS 설정, cassandra db 적재시 TTL 설정, GCS bucket의 TTL 설정


---
#### Kafka
##### Kafka cluster
- 3개의 서버, 3개의 노드로 클러스터 구성
- 카프카: 내결함성, 로드밸런싱을 통한 처리량 증가
- 주키퍼: 주키퍼의 쿼럼 기반 시스템으로 인해 가용성을 위해 주키퍼 앙상블을 3개의 노드로 구성
##### Data Lifecycle
- RETENTION_HOURS을 24로 설정함으로 인해 최근 24시간 동안의 데이터만 보관
##### Topic Replication Factor 
- topic replication factor가 2일 경우: 1개의 노드 장애 발생 시 데이터 유실 없음, 2개의 노드 장애 발생시 데이터 유실 발생
- topic replication factor가 3일 경우: 2개의 노드 장애 발생시에도 데이터 유실 없음
- 데이터 유실과 서버 리소스 사용 사이의 trade off를 고려해 topic replication을 2로 설정
- topic replication factor ⬆: 브로커의 장애 시 데이터 유실 확률 ️⬇️, 디스크 저장 공간 사용⬆, 네트워크 트래픽⬆
##### Producer Ack
- 실시간 스트림 데이터의 토픽의 경우 처리량이 중요하지만 리더 파티션에 적상적으로 적재되었는지 최소한의 응답을 확인하기 위해 ack = 1(기본값)으로 설정


> 카프카의 복제본과 내결함성으로 여러 노드에 복제본을 저장해두어 토픽의 리더, 팔로워에서 리더가 죽더라도 다른 팔로워가 리더가 되어 내결함성을 유지할 수 있음

> 주키퍼는 분산 애플리케이션에서의 메타 데이터 관리, 동기화, 그룹서비스 등을 제공함, 주키퍼를 이용해 브로커 상태를 추적하고 토픽 및 파티션 메타데이터를 저장한다.
> 주키퍼 앙상블은 가용성과 내 결함성을 위해 최소 3개 이상의 홀수로 구성하는 것이 좋다. 주키퍼는 쿼럼(quorum, 과반수) 기반 시스템으로 서비스를 계속 제공하기 위해 쿼럼을 유지해야한다. ex) 2개의 노드에서 하나가 실패하면, 쿼럼을 유지할 수 없게 되어 서비스가 중단된다.

#### cassandra 클러스터
- 카산드라를 왜 선택했는가
- 3개의 노드(가용성, 로드 밴런싱)
-- master slave 구조가 아닌 동등함, 쓰기 분산을 위해
- 파티션 구성
- 일관성 level은 ~~한 이유로 이렇게 유지(처리량 중심)


#### Spark
- 스파크 ui를 보면서 ~~한 최적화
- 

#### grafana
- ~~한 이유로 그라파나 선택(선택지 ~~~가 있었음)
- 이렇게 실시간과 스트림 데이터(카산드라 빅쿼리 데이터 가져올 수 있게 대시보드)

| 제품 | 유료, 무료 |
| ------ | ------ |
| Dropbox | [plugins/dropbox/README.md][PlDb] |
| GitHub | [plugins/github/README.md][PlGh] |
| Google Drive | [plugins/googledrive/README.md][PlGd] |
| OneDrive | [plugins/onedrive/README.md][PlOd] |
| Medium | [plugins/medium/README.md][PlMe] |
| Google Analytics | [plugins/googleanalytics/README.md][PlGa] |

### bigquery
- 빅쿼리 파티션 어떻게 구성했음
-
Markdown is a lightweight markup language based on the formatting conventions
that people naturally use in email.
As [John Gruber] writes on the [Markdown site][df1]

> The overriding design goal for Markdown's
> formatting syntax is to make it as readable
> as possible. The idea is that a
> Markdown-formatted document should be
> publishable as-is, as plain text, without
> looking like it's been marked up with tags
> or formatting instructions.

### 플젝하면서 어렸웠던 점
- 1. 실시간 스트림의 처리량을 감당하는것 (카산드라)
- 2. 클러스터 구성, 가용성 확보 및 로드밸런싱을 위해 클러스터를 구성했는데 막상 이게 잘 동작하는지 모르겠음(따라서 하나의 노드들을 종료시켜봄
-- 1) 카프카 active controller 브로커를 종료시켰을 때 새로운 브로커가 active controller가 되는가

This text you see here is *actually- written in Markdown! To get a feel
for Markdown's syntax, type some text into the left window and
watch the results in the right.

## Tech

Dillinger uses a number of open source projects to work properly:

- [AngularJS] - HTML enhanced for web apps!
- [Ace Editor] - awesome web-based text editor
- [markdown-it] - Markdown parser done right. Fast and easy to extend.
- [Twitter Bootstrap] - great UI boilerplate for modern web apps
- [node.js] - evented I/O for the backend
- [Express] - fast node.js network app framework [@tjholowaychuk]
- [Gulp] - the streaming build system
- [Breakdance](https://breakdance.github.io/breakdance/) - HTML
to Markdown converter
- [jQuery] - duh

And of course Dillinger itself is open source with a [public repository][dill]
 on GitHub.

## Installation

Dillinger requires [Node.js](https://nodejs.org/) v10+ to run.

Install the dependencies and devDependencies and start the server.

```sh
cd dillinger
npm i
node app
```

For production environments...

```sh
npm install --production
NODE_ENV=production node app
```

## Plugins

Dillinger is currently extended with the following plugins.
Instructions on how to use them in your own application are linked below.

| Plugin | README |
| ------ | ------ |
| Dropbox | [plugins/dropbox/README.md][PlDb] |
| GitHub | [plugins/github/README.md][PlGh] |
| Google Drive | [plugins/googledrive/README.md][PlGd] |
| OneDrive | [plugins/onedrive/README.md][PlOd] |
| Medium | [plugins/medium/README.md][PlMe] |
| Google Analytics | [plugins/googleanalytics/README.md][PlGa] |

## Development

Want to contribute? Great!

Dillinger uses Gulp + Webpack for fast developing.
Make a change in your file and instantaneously see your updates!

Open your favorite Terminal and run these commands.

First Tab:

```sh
node app
```

Second Tab:

```sh
gulp watch
```

(optional) Third:

```sh
karma test
```

#### Building for source

For production release:

```sh
gulp build --prod
```

Generating pre-built zip archives for distribution:

```sh
gulp build dist --prod
```

## Docker

Dillinger is very easy to install and deploy in a Docker container.

By default, the Docker will expose port 8080, so change this within the
Dockerfile if necessary. When ready, simply use the Dockerfile to
build the image.

```sh
cd dillinger
docker build -t <youruser>/dillinger:${package.json.version} .
```

This will create the dillinger image and pull in the necessary dependencies.
Be sure to swap out `${package.json.version}` with the actual
version of Dillinger.

Once done, run the Docker image and map the port to whatever you wish on
your host. In this example, we simply map port 8000 of the host to
port 8080 of the Docker (or whatever port was exposed in the Dockerfile):

```sh
docker run -d -p 8000:8080 --restart=always --cap-add=SYS_ADMIN --name=dillinger <youruser>/dillinger:${package.json.version}
```

> Note: `--capt-add=SYS-ADMIN` is required for PDF rendering.

Verify the deployment by navigating to your server address in
your preferred browser.

```sh
127.0.0.1:8000
```

## License

MIT

**Free Software, Hell Yeah!**

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)

   [dill]: <https://github.com/joemccann/dillinger>
   [git-repo-url]: <https://github.com/joemccann/dillinger.git>
   [john gruber]: <http://daringfireball.net>
   [df1]: <http://daringfireball.net/projects/markdown/>
   [markdown-it]: <https://github.com/markdown-it/markdown-it>
   [Ace Editor]: <http://ace.ajax.org>
   [node.js]: <http://nodejs.org>
   [Twitter Bootstrap]: <http://twitter.github.com/bootstrap/>
   [jQuery]: <http://jquery.com>
   [@tjholowaychuk]: <http://twitter.com/tjholowaychuk>
   [express]: <http://expressjs.com>
   [AngularJS]: <http://angularjs.org>
   [Gulp]: <http://gulpjs.com>

   [PlDb]: <https://github.com/joemccann/dillinger/tree/master/plugins/dropbox/README.md>
   [PlGh]: <https://github.com/joemccann/dillinger/tree/master/plugins/github/README.md>
   [PlGd]: <https://github.com/joemccann/dillinger/tree/master/plugins/googledrive/README.md>
   [PlOd]: <https://github.com/joemccann/dillinger/tree/master/plugins/onedrive/README.md>
   [PlMe]: <https://github.com/joemccann/dillinger/tree/master/plugins/medium/README.md>
   [PlGa]: <https://github.com/RahulHP/dillinger/blob/master/plugins/googleanalytics/README.md>
