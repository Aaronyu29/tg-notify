# Fiddler 抓包 Claude Code CLI 请求指南

## 目录
- [环境说明](#环境说明)
- [前置准备](#前置准备)
- [配置步骤](#配置步骤)
- [抓包流程](#抓包流程)
- [数据分析](#数据分析)
- [常见问题](#常见问题)

---

## 环境说明

### 测试环境
- **操作系统**: Windows 10/11
- **抓包工具**: Fiddler Classic
- **目标程序**: Claude Code CLI
- **Shell 环境**: PowerShell / CMD / Git Bash

### 关键发现
- Claude Code 基于 Node.js 运行
- 默认不使用系统代理，需要通过环境变量强制
- 使用 HTTPS 加密通信，需要配置证书信任

---

## 前置准备

### 1. 安装 Fiddler Classic

下载地址: https://www.telerik.com/fiddler/fiddler-classic

### 2. 配置 Fiddler

#### 2.1 基础连接设置

**Tools → Options → Connections**

```
✅ Fiddler listens on port: 8888
✅ Allow remote computers to connect
✅ Act as system proxy on startup
✅ Monitor all connections
```

**Bypass 列表**（可选）：
- 清空或保留 `<loopback>` 根据需要

#### 2.2 HTTPS 解密设置

**Tools → Options → HTTPS**

```
✅ Decrypt HTTPS traffic
✅ Ignore server certificate errors (unsafe)
```

**安装证书**：
1. 点击 **Actions** → **Trust Root Certificate**
2. 确认安装 Fiddler 根证书到系统信任区

#### 2.3 重启 Fiddler

配置完成后重启 Fiddler 使设置生效。

---

## 配置步骤

### 方法 1: PowerShell 环境（推荐）

#### 步骤 1: 关闭当前 Claude Code 会话

在运行 Claude Code 的终端中按 `Ctrl+C` 退出。

#### 步骤 2: 设置代理环境变量

在 **同一个 PowerShell 终端**中执行：

```powershell
# 设置 HTTP/HTTPS 代理
$env:HTTP_PROXY="http://127.0.0.1:8888"
$env:HTTPS_PROXY="http://127.0.0.1:8888"

# 忽略 SSL 证书验证（允许 Fiddler 中间人证书）
$env:NODE_TLS_REJECT_UNAUTHORIZED="0"

# 验证设置
echo "HTTP_PROXY=$env:HTTP_PROXY"
echo "HTTPS_PROXY=$env:HTTPS_PROXY"
echo "NODE_TLS_REJECT_UNAUTHORIZED=$env:NODE_TLS_REJECT_UNAUTHORIZED"
```

#### 步骤 3: 启动 Claude Code

```powershell
claude
```

**重要提示**：
- ⚠️ 环境变量**仅在当前 PowerShell 进程有效**
- ⚠️ 必须在**设置环境变量后**启动 Claude Code
- ⚠️ 关闭终端后设置失效

---

### 方法 2: CMD 环境

```cmd
REM 设置代理
set HTTP_PROXY=http://127.0.0.1:8888
set HTTPS_PROXY=http://127.0.0.1:8888
set NODE_TLS_REJECT_UNAUTHORIZED=0

REM 验证设置
echo HTTP_PROXY=%HTTP_PROXY%
echo HTTPS_PROXY=%HTTPS_PROXY%

REM 启动 Claude Code
claude
```

---

### 方法 3: Git Bash / WSL 环境

```bash
# 设置代理
export HTTP_PROXY="http://127.0.0.1:8888"
export HTTPS_PROXY="http://127.0.0.1:8888"
export NODE_TLS_REJECT_UNAUTHORIZED="0"

# 如果是 WSL2，需要使用 Windows 主机 IP
export WINDOWS_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
export HTTP_PROXY="http://$WINDOWS_IP:8888"
export HTTPS_PROXY="http://$WINDOWS_IP:8888"

# 验证设置
echo "HTTP_PROXY=$HTTP_PROXY"
echo "HTTPS_PROXY=$HTTPS_PROXY"

# 启动 Claude Code
claude
```

---

## 抓包流程

### 1. 启动 Fiddler

确保 Fiddler 正在运行并处于捕获状态（顶部无黄色警告条）。

### 2. 清空现有记录

点击 Fiddler 工具栏的 **Remove All** 或按 `Ctrl+X`。

### 3. 触发 Claude Code 请求

在 Claude Code 中执行任何操作，例如：
- 发送消息
- 执行命令
- 使用工具

### 4. 观察 Fiddler 捕获

在 Fiddler 左侧会话列表中查找：

**关键特征**：
- **Host**: `api.claude.ai` 或 `api.anthropic.com`
- **Process**: `node.exe:xxxxx`
- **Protocol**: HTTPS
- **Method**: POST
- **Path**: `/v1/messages` 或类似

### 5. 保存会话

**File → Save → All Sessions**

保存为 `.saz` 文件（Fiddler Session Archive）。

---

## 数据分析

### SAZ 文件结构

`.saz` 文件本质是 **ZIP 压缩包**，包含：

```
ws1.saz
├── [Content_Types].xml    # MIME 类型定义
├── _index.htm             # 会话索引页面
└── raw/                   # 原始数据目录
    ├── 001_c.txt          # Client request（请求）
    ├── 001_s.txt          # Server response（响应）
    ├── 001_m.xml          # Metadata（元数据）
    ├── 002_c.txt
    ├── 002_s.txt
    ├── 002_m.xml
    └── ...
```

### 文件命名规则

- **`XXX_c.txt`**: 客户端请求（请求头 + 请求体）
- **`XXX_s.txt`**: 服务器响应（响应头 + 响应体）
- **`XXX_m.xml`**: 元数据（时间戳、进程、URL、TLS 信息）

### 解压 SAZ 文件

#### 方法 1: 在 Fiddler 中打开

```bash
# Windows
start ws1.saz

# 或直接拖拽到 Fiddler 窗口
```

#### 方法 2: 手动解压

```powershell
# PowerShell
Copy-Item ws1.saz ws1.zip
Expand-Archive -Path ws1.zip -DestinationPath ws1_extracted
```

```bash
# Linux/Mac
cp ws1.saz ws1.zip
unzip ws1.zip -d ws1_extracted
```

### 查找 Claude API 请求

```bash
# 搜索包含 Claude API 的请求
cd ws1_extracted/raw
grep -i "api.claude.ai\|anthropic.com" *.xml

# 查找非浏览器进程的请求
grep "x-processinfo" *.xml | grep -v "chrome\|edge"

# 查找 node.exe 进程的请求
grep "node.exe" *.xml
```

### 查看请求详情

#### 查看元数据

```bash
cat 001_m.xml
```

关键字段：
- `x-processinfo`: 进程名和 PID
- `https-client-snihostname`: 目标域名
- `ClientConnected`: 连接时间
- `x-hostip`: 服务器 IP

#### 查看请求内容

```bash
cat 001_c.txt
```

包含：
- HTTP 方法和路径
- 请求头（Headers）
- 请求体（Body）- JSON 格式

#### 查看响应内容

```bash
cat 001_s.txt
```

包含：
- HTTP 状态码
- 响应头（Headers）
- 响应体（Body）- JSON 格式

### 在 Fiddler 中查看

1. 双击 `.saz` 文件在 Fiddler 中打开
2. 点击左侧会话列表中的请求
3. 右侧标签页：
   - **Inspectors → Headers**: 查看请求/响应头
   - **Inspectors → TextView**: 文本格式查看
   - **Inspectors → JSON**: JSON 格式化显示
   - **Inspectors → Raw**: 原始数据

---

## 常见问题

### Q1: Fiddler 没有捕获到 Claude Code 的流量

**可能原因**：
1. ❌ 环境变量设置后没有重启 Claude Code
2. ❌ 在不同的终端窗口启动了 Claude Code
3. ❌ HTTPS 解密未配置
4. ❌ Claude Code 使用了证书固定（Certificate Pinning）

**解决方案**：
```powershell
# 1. 确认环境变量已设置
echo $env:HTTP_PROXY
echo $env:HTTPS_PROXY

# 2. 确认 Fiddler 正在运行
netstat -ano | findstr :8888

# 3. 重启 Claude Code（在同一终端）
# Ctrl+C 退出，然后重新运行 claude

# 4. 检查 Fiddler 是否处于捕获状态
# 顶部应无黄色警告条
```

### Q2: 抓到的都是浏览器流量

**原因**：
- 抓包时间段内，Claude Code 没有发送请求
- 或者 Claude Code 没有使用代理

**解决方案**：
1. 确保在 Claude Code 中执行了操作（发送消息、运行命令）
2. 在 Fiddler 中过滤进程：
   - **Filters** 标签
   - **Process Filter** → 选择 `node.exe`

### Q3: 看到的是加密数据

**原因**：
- HTTPS 解密未启用
- 证书未安装

**解决方案**：
1. **Tools → Options → HTTPS**
2. 勾选 **Decrypt HTTPS traffic**
3. 点击 **Actions → Trust Root Certificate**
4. 重启 Fiddler
5. **重新抓包**（已抓取的加密流量无法事后解密）

### Q4: WSL 环境无法抓包

**原因**：
- WSL 的 `127.0.0.1` 指向 WSL 内部，不是 Windows 主机

**解决方案**：
```bash
# 获取 Windows 主机 IP
export WINDOWS_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')

# 使用 Windows IP 作为代理
export HTTP_PROXY="http://$WINDOWS_IP:8888"
export HTTPS_PROXY="http://$WINDOWS_IP:8888"

# Fiddler 需要允许远程连接
# Tools → Options → Connections → Allow remote computers to connect
```

### Q5: 证书错误导致请求失败

**原因**：
- Node.js 拒绝 Fiddler 的自签名证书

**解决方案**：
```powershell
# 临时禁用 SSL 验证（仅用于调试）
$env:NODE_TLS_REJECT_UNAUTHORIZED="0"
```

⚠️ **安全警告**：
- 此设置会禁用所有 SSL 证书验证
- 仅在本地调试时使用
- 不要在生产环境使用

### Q6: 环境变量设置后仍无效

**检查清单**：
```powershell
# 1. 验证环境变量
Get-ChildItem Env: | Where-Object { $_.Name -like "*PROXY*" }

# 2. 检查 Claude Code 进程
tasklist | findstr node.exe

# 3. 测试代理连接
curl -x http://127.0.0.1:8888 http://www.example.com

# 4. 查看 Fiddler 日志
# Fiddler → Log 标签
```

---

## 高级技巧

### 1. 过滤特定请求

**Fiddler → Filters 标签**

```
✅ Use Filters
Process: node.exe
Host: api.claude.ai
```

### 2. 自动保存会话

**Rules → Customize Rules**

添加：
```javascript
static function OnBeforeResponse(oSession: Session) {
    if (oSession.hostname.Contains("claude.ai")) {
        oSession["ui-backcolor"] = "yellow";
    }
}
```

### 3. 导出为 HAR 格式

**File → Export Sessions → HTTP Archive (HAR)**

HAR 格式可用于：
- Chrome DevTools 导入
- 自动化测试工具
- 性能分析工具

### 4. 使用 Wireshark 抓包（备选方案）

如果 Fiddler 无法抓包，可以使用 Wireshark：

```bash
# 过滤 Claude API 流量
tcp.port == 443 and (http.host contains "claude.ai" or http.host contains "anthropic.com")
```

**注意**：Wireshark 无法解密 HTTPS 流量，除非配置 SSLKEYLOGFILE。

---

## 安全注意事项

### ⚠️ 重要警告

1. **证书信任风险**
   - Fiddler 根证书允许中间人攻击
   - 仅在受信任的网络环境使用
   - 调试完成后卸载证书

2. **敏感数据泄露**
   - SAZ 文件包含完整的请求/响应
   - 可能包含 API Key、Token、个人信息
   - 不要分享或上传 SAZ 文件

3. **禁用 SSL 验证**
   - `NODE_TLS_REJECT_UNAUTHORIZED=0` 会禁用所有证书验证
   - 仅在本地调试时使用
   - 使用后立即恢复

### 清理步骤

```powershell
# 1. 删除环境变量
Remove-Item Env:HTTP_PROXY
Remove-Item Env:HTTPS_PROXY
Remove-Item Env:NODE_TLS_REJECT_UNAUTHORIZED

# 2. 卸载 Fiddler 证书
# Tools → Options → HTTPS → Actions → Remove Interception Certificates

# 3. 删除敏感的 SAZ 文件
Remove-Item *.saz -Force
```

---

## 参考资料

- [Fiddler 官方文档](https://docs.telerik.com/fiddler)
- [Node.js 代理配置](https://nodejs.org/api/http.html#http_http_request_options_callback)
- [HTTP Archive (HAR) 格式](http://www.softwareishard.com/blog/har-12-spec/)
- [Wireshark 用户指南](https://www.wireshark.org/docs/wsug_html_chunked/)

---

## 更新日志

- **2026-01-09**: 初始版本，基于 Windows + PowerShell 环境测试
- 包含 PowerShell、CMD、Git Bash、WSL 多种环境的配置方法
- 添加 SAZ 文件结构和分析方法
- 补充常见问题和解决方案

---

## 贡献

如有问题或改进建议，请提交 Issue 或 Pull Request。
