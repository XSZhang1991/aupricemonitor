@echo off
REM 黄金监控系统 - GitHub推送脚本
REM 使用方法: 双击运行此脚本

cd /d "%~dp0"

echo.
echo ===================================
echo  黄金价格与波动率监控系统
echo  GitHub 推送脚本
echo ===================================
echo.

REM 检查Git是否安装
git --version > nul 2>&1
if errorlevel 1 (
    echo 错误: Git未安装或不在系统路径中
    echo 请访问 https://git-scm.com/download/win 下载安装Git
    pause
    exit /b 1
)

echo 正在推送代码到GitHub...
echo.

REM 创建新Token的提示
echo 如果遇到验证错误，请:
echo 1. 访问 https://github.com/settings/tokens
echo 2. 生成新的 Personal Access Token (至少需要 repo 权限)
echo 3. 复制Token并在出现提示时粘贴
echo.

REM 执行推送
git push -u origin master

if errorlevel 1 (
    echo.
    echo 推送失败！
    echo.
    echo 可能的原因:
    echo   1. Token过期或无效
    echo   2. 仓库URL错误
    echo   3. 网络连接问题
    echo.
    echo 请检查以下内容:
    echo   - GitHub仓库是否正确创建
    echo   - Token是否有效和足够的权限
    echo   - 网络连接是否正常
    echo.
) else (
    echo.
    echo 推送成功！
    echo 代码已上传到 GitHub
    echo.
)

pause
