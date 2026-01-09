在启动 Claude CLI 或 VS Code 插件之前，需要先准备 4 个环境变量。推荐一次性配置在 shell/系统设置里，并在修改后重新打开终端或编辑器，这样每个新会话都会自动继承。

Windows
以下任意方式都可以完成同样的配置：

方式 1 · GUI（推荐，永久生效）

按 Win + R，输入 sysdm.cpl 并回车。
打开 高级 → 环境变量。
在 用户变量 中点击 新建，逐个添加：
ANTHROPIC_BASE_URL → https://www.claudeide.net/api/anthropic
ANTHROPIC_AUTH_TOKEN → test
API_TIMEOUT_MS → 600000
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC → 1
关闭所有窗口，重启终端或 IDE。
方式 2 · 命令提示符（永久）

Copy
setx ANTHROPIC_BASE_URL "https://www.claudeide.net/api/anthropic"
setx ANTHROPIC_AUTH_TOKEN "test"
setx API_TIMEOUT_MS "600000"
setx CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC "1"

方式 3 · PowerShell（永久）

Copy
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_BASE_URL', 'https://www.claudeide.net/api/anthropic', 'User')
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', 'test', 'User')
[System.Environment]::SetEnvironmentVariable('API_TIMEOUT_MS', '600000', 'User')
[System.Environment]::SetEnvironmentVariable('CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC', '1', 'User')


方式 3 · 临时会话（只对当前 CMD 窗口生效）

Copy
set ANTHROPIC_BASE_URL=https://www.claudeide.net/api/anthropic
set ANTHROPIC_AUTH_TOKEN=test
set API_TIMEOUT_MS=600000
set CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1


启动 Claude 编码环境
在任意项目目录中运行：

Copy
cd your-project
claude
成功启动后将出现类似界面：



若使用 VS Code（或其他 IDE）插件，也需要上述环境变量。若看到如下提示：



说明插件没有读到配置，需要重新检查。也可以直接在配置文件里写死这些值：

Claude 全局设置

macOS/Linux：~/.claude/settings.json
Windows：C:/Users/<UserName>/.claude/settings.json
内容示例：
Copy
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "test",
    "ANTHROPIC_BASE_URL": "https://www.claudeide.net/api/anthropic",
    "API_TIMEOUT_MS": "600000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
  }
}
VS Code settings.json – 添加：

Copy
"claudeCode.environmentVariables": [
  { "name": "ANTHROPIC_BASE_URL", "value": "https://www.claudeide.net/api/anthropic" },
  { "name": "ANTHROPIC_AUTH_TOKEN", "value": "test" }
],
修改后请重新加载 VS Code 或重启终端。

我同时配置了方式1 GUI 方式2 方式3 以及后面这两个全局配置

 (并且配置的内容都是一致的，auth_token 可能不一致，你帮我检查下，我检查应该一样。然后对话容易隔一会就出现需要 /login 的操作。
怎么时候？

> Q1 A Q2 A Q3 排除其他临时文件和敏感文件，md 和 py 文件应提交。 Q4 B 
  ⎿  API Error: 403 status code (no body) · Please run /login

> Q1 A Q2 A Q3 排除其他临时文件和敏感文件，md 和 py 文件应提交。 Q4 B 
  ⎿  API Error: 403 status code (no body) · Please run /login

> Q1 A Q2 A Q3 排除其他临时文件和敏感文件，md 和 py 文件应提交。 Q4 B 
  ⎿  API Error: 403 status code (no body) · Please run /login
> 
类似上面这样。是不是我应该删掉重复的配置呢？