# 部署说明

## A. Streamlit Community Cloud（优先）

### 1. 建立GitHub仓库

1. 在GitHub新建仓库，将本包根目录中的全部文件推送到`main`分支。
2. 确认`app.py`、`requirements.txt`、`packages.txt`位于仓库根目录，配置文件位于`.streamlit/config.toml`。
3. 推送前检查GitHub的Files列表，确认没有`.xlsx`、`.zip`、`secrets.toml`、`uploads/`或`output/`。

示例命令：

```bash
git init
git add .
git commit -m "Deploy aviation market dashboard"
git branch -M main
git remote add origin https://github.com/<account>/<repository>.git
git push -u origin main
```

### 2. 创建在线应用

1. 访问[share.streamlit.io](https://share.streamlit.io/)，使用GitHub登录。
2. 选择Create app，填写GitHub仓库、`main`分支和主文件`app.py`。
3. 在Advanced settings中选择Python 3.12。本项目不需要secrets。
4. 点击Deploy。Community Cloud会从`requirements.txt`安装Python依赖，从`packages.txt`安装Linux字体。
5. 部署完成后复制`https://<your-subdomain>.streamlit.app`分享给使用者。

Community Cloud从仓库根目录执行应用，因此不要改变上述相对路径。更新GitHub的`main`分支后，线上应用会自动更新；修改依赖文件会触发完整重新部署。

当前依赖将Streamlit固定为`1.50.0`并使用Python 3.12。固定版本避免云端自动升级改变前端资源分块；升级前应先在测试分支完成真实Excel和无痕浏览器验收。

### 3. 上线验收

1. 使用含有两个必需Sheet的Excel生成F01—F07、A01—A03、T01—T04；缺少方向Sheet时应明确只跳过F07、T03、T04。
2. 对F01、A01、F05、F06、F07、T01—T04依次测试单年、2018—2021和完整时期，确认图、KPI、表格及下载随参数变化；单年F06应显示方法提示。
3. 测试CHN、USA、IND、ETH、KEN、ZMB的国家搜索、指数基期、方向结构和国家年度查询。
4. 输入非预设Top N（例如25），下载一张PNG、一份图数据CSV、一份TopN CSV和完整排名XLSX，确认文件名和内容参数一致。
5. 上传一份同名但数值已修改的Excel，确认页面内容指纹和结果变化，不显示上一份数据。
6. 用两个无痕浏览器窗口分别上传不同Excel，确认文件名、指标和下载结果彼此独立，且正式结果区无动态模块加载错误。
7. 点击“清除本次会话数据”，确认页面回到上传状态。

### 4. 公开与私密访问

- 公开应用：任何拿到网址的人都可使用，适合公开数据和教学展示。
- 私密应用：在Community Cloud的Sharing设置中限定访问者，适合内部评审。
- 浏览器到Community Cloud的传输使用HTTPS。对严格保密、不允许第三方云处理的数据，使用下方的自管Linux服务器方案。

## B. Linux云服务器 / Docker

建议资源：2 vCPU、4 GB内存；多人同时生成全部高分辨率图时增加内存。

```bash
docker compose up -d --build
docker compose ps
```

默认访问`http://<server-ip>:8501`。正式环境应使用Nginx或云负载均衡器终止HTTPS，并只开放443端口。Docker配置使用：

- 非root运行；
- 容器文件系统只读；
- `/tmp`使用临时内存盘；
- 不挂载上传或结果持久化目录；
- 健康检查访问`/_stcore/health`。

升级时：

```bash
git pull
docker compose up -d --build
```

## C. 数据和运维边界

- 应用不保存上传Excel或结果。用户应在会话结束前下载需要的文件。
- 会话断开、应用休眠、重启或重部署后，内存数据会丢失。
- Community Cloud资源有限，高并发或长期稳定运行应迁移至受控Linux服务器。
- 异常页面只显示诊断编号，详细堆栈仅在管理员日志中。

## 官方参考

- [Streamlit Community Cloud文件组织](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization)
- [Community Cloud依赖管理](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
- [Community Cloud部署流程](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app)
- [Community Cloud信任与安全](https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/trust-and-security)
