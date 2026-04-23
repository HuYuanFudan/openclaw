# financialKG

金融知识图谱前后端仓库。

- 前端：`front/`（Vue 3 + Element Plus + axios）
- 后端：`knowledgegraph/`（Django + DRF + Neo4j + SQLite）
- 详细分析报告：[`knowledgegraph/仓库详细分析报告.md`](knowledgegraph/仓库详细分析报告.md)

## 仓库结构

```text
financialKG/
├── front/          # 前端项目
└── knowledgegraph/ # 后端项目
```

## 运行前准备

你至少需要准备：

- Python 3
- pip
- Node.js 与 npm
- 可访问的 Neo4j 实例

当前仓库**没有**提供 `Dockerfile`、`docker-compose` 或 `.env` 文件；很多配置仍写死在代码里。

## 后端启动

```bash
cd /home/ubuntu/code/financialKG/knowledgegraph
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8001
```

说明：

- 这里建议先跑在 `8001`，因为当前前端很多页面把后端地址直接写成了 `:8001`，例如 `front/src/views/Login_neo4j.vue:66`、`front/src/views/QueryNode.vue:149`。
- 如果你改成 `8000` 或其他端口，需要同步调整前端页面里的硬编码地址。

### 可选：初始化默认用户

仅在**全新 SQLite 数据库**场景下再执行：

```bash
cd /home/ubuntu/code/financialKG/knowledgegraph
source .venv/bin/activate
python manage.py create_custom_users
```

注意：

- 该命令定义在 `knowledgegraph/knowledgegraph/management/commands/create_custom_users.py:4`。
- 如果数据库里已经有这些用户，就不要重复执行。

## 前端启动

```bash
cd /home/ubuntu/code/financialKG/front
npm install
npm run serve
```

前端构建命令：

```bash
cd /home/ubuntu/code/financialKG/front
npm run build
```

## 当前可见的主要页面

路由定义见 `front/src/router/index.js:12`：

- `/login`
- `/home`
- `/addnode`
- `/querynode`
- `/deletenode`
- `/queryrelationship`
- `/allgraph`
- `/allmetaknowledge`
- `/addmetaknowledge`
- `/formula`

## 推荐的本地联调方式

当前仓库最接近“可直接体验”的方式是：

1. 先启动 Django，并监听 `8001`
2. 再启动 Vue 开发服务器
3. 打开前端登录页，先验证登录、查节点、查关系、元知识列表这几条主链路

## 使用时必须注意的几个问题

### 1. 前端接口地址没有统一

虽然 `front/src/main.js:17` 设置了 axios `baseURL`，但很多页面没有使用它，而是直接写死地址，例如：

- `front/src/views/Login_neo4j.vue:66`
- `front/src/views/AllMetaknowledge.vue:81`
- `front/src/views/AddNode.vue:103`
- `front/src/views/QueryRelationship.vue:110`

如果你不是在原来的固定服务器环境运行，通常需要把这些地址改成你当前机器的地址。

### 2. 本地开发可能会遇到 CORS

当前后端 CORS 白名单在 `knowledgegraph/knowledgegraph/settings.py:27`，只允许固定来源，不包含常见的 `http://localhost:8080`。

如果你本地直接 `npm run serve`，很可能还需要把你的前端地址加进 CORS 白名单。

### 3. 登录 token 键名不一致

- `front/src/main.js:11` 读取 `jwt_token`
- `front/src/views/Login_neo4j.vue:72` 写入 `access_token`
- `front/src/router/index.js:77` 也读取 `access_token`

这会导致刷新页面后，请求头和登录态判断可能不一致。

### 4. 不要直接使用旧的元知识初始化脚本

`knowledgegraph/knowledgegraph/management/commands/create_metaknowledge.py:25` 仍在引用已经删除的字段，不适合作为当前初始化方案。

## 部署相关提醒

- `knowledgegraph/uwsgi.ini:4` 仍是旧机器绝对路径，部署前必须先改。
- 后端里还存在硬编码的 Neo4j 连接配置：`knowledgegraph/knowledgegraph/views.py:37`。
- Django `SECRET_KEY` 也直接写在 `knowledgegraph/knowledgegraph/settings.py:18`。

## 建议你先看什么

如果你刚接手这个仓库，建议按下面顺序阅读：

1. `README.md`
2. `front/src/router/index.js`
3. `front/src/main.js`
4. `knowledgegraph/knowledgegraph/urls.py`
5. `knowledgegraph/knowledgegraph/views.py`
6. `knowledgegraph/仓库详细分析报告.md`
