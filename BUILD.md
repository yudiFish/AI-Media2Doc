# 镜像构建和推送

## 快速开始

### 构建并推送镜像到 Harbor

```bash
# 推送 latest 版本
./build-and-push.sh

# 推送指定版本
./build-and-push.sh v1.0.0
```

### 前置条件

1. **Docker 已安装并运行**
2. **已登录 Harbor 仓库**
   ```bash
   docker login www.harbor.wymhealth.cloud:8443
   ```

## 使用说明

### 脚本功能

`build-and-push.sh` 脚本会自动完成以下操作：

1. ✅ 使用 `docker-compose build` 构建本地镜像
2. ✅ 为镜像打标签（添加 Harbor 仓库前缀）
3. ✅ 推送镜像到私有 Harbor 仓库

### 镜像命名规则

- **后端镜像**: `www.harbor.wymhealth.cloud:8443/app/ai-media2doc-backend:VERSION`
- **前端镜像**: `www.harbor.wymhealth.cloud:8443/app/ai-media2doc-frontend:VERSION`

默认版本为 `latest`，可通过参数指定版本号。

### 使用示例

```bash
# 1. 登录 Harbor（首次使用需要）
docker login www.harbor.wymhealth.cloud:8443

# 2. 构建并推送 latest 版本
./build-and-push.sh

# 3. 构建并推送指定版本
./build-and-push.sh v1.0.0
./build-and-push.sh v2.1.3
```

## 部署配置

推送镜像后，修改部署环境的 `docker-compose.yaml`：

```yaml
services:
  backend:
    image: www.harbor.wymhealth.cloud:8443/app/ai-media2doc-backend:latest
    # ... 其他配置

  frontend:
    image: www.harbor.wymhealth.cloud:8443/app/ai-media2doc-frontend:latest
    # ... 其他配置
```

## 常见问题

### 1. 推送失败：unauthorized

**原因**: 未登录 Harbor 或登录已过期

**解决**:
```bash
docker login www.harbor.wymhealth.cloud:8443
# 输入用户名和密码
```

### 2. 构建失败

**检查事项**:
- ✅ Docker 是否正常运行
- ✅ `variables.env` 文件是否存在且配置正确
- ✅ 网络连接是否正常（安装依赖需要网络）

### 3. 如何查看已推送的镜像

访问 Harbor Web UI：
```
https://www.harbor.wymhealth.cloud:8443
```

进入 `app` 项目查看镜像列表。

## 维护

### 查看本地镜像

```bash
docker images | grep ai-media2doc
```

### 删除旧版本镜像

```bash
# 删除本地镜像
docker rmi ai-media2doc-backend:local
docker rmi ai-media2doc-frontend:local

# 删除 Harbor 镜像（通过 Harbor Web UI 操作）
```

### 版本管理建议

- `latest` - 最新开发版本
- `v1.0.0` - 稳定发布版本
- `dev` - 开发测试版本
- `prod` - 生产环境版本
