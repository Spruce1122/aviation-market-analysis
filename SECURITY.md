# 数据安全说明

## 处理方式

应用使用`UploadedFile.getvalue()`取得当前会话的Excel字节，并通过`BytesIO`在内存中读取。数据校验、派生指标、Matplotlib图形、Excel表和ZIP均保存在该Streamlit会话的`session_state`或局部内存中。

## 隔离措施

- 不使用`st.cache_data`或`st.cache_resource`缓存用户数据。
- 不使用全局DataFrame、全局文件字节或全局结果ZIP。
- 不创建`uploads/`、`output/`或按用户文件名命名的服务器文件。
- 文件指纹用于当前会话的更新识别，不用于跨会话检索。
- 不在终端日志中输出Excel内容、国家明细或完整文件指纹。
- 结果生成异常统一显示“当前结果暂时无法生成，请检查数据覆盖范围”，详细堆栈仅进入管理员日志。

## 会话结束

点击“清除本次会话数据”会释放当前会话的工作簿派生对象、图形和ZIP。用户关闭会话、服务器重启或Community Cloud休眠后，内存中的未下载结果不可恢复。

## 部署责任

Community Cloud是第三方云运行环境。严格保密数据应部署在单位控制的Linux服务器中，配置HTTPS、访问控制、审计日志和定期安全更新。
