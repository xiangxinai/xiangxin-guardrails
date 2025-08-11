# 贡献指南 Contributing Guide

感谢您对象信AI安全护栏项目的关注！我们欢迎并非常感谢任何形式的贡献。

Thank you for your interest in Xiangxin AI Guardrails! We welcome and greatly appreciate contributions of all kinds.

[中文](#中文版本) | [English](#english-version)

## 中文版本

### 如何贡献

我们欢迎以下类型的贡献：

#### 🐛 Bug报告
- 在使用过程中发现的任何问题
- 文档中的错误或不准确信息
- 性能问题或异常行为

#### 💡 功能建议
- 新功能的想法和建议
- 现有功能的改进建议
- 用户体验优化建议

#### 📖 文档改进
- 修正文档错误
- 添加使用示例
- 翻译文档到其他语言
- 改进代码注释

#### 💻 代码贡献
- Bug修复
- 新功能开发
- 性能优化
- 测试用例添加

### 开发环境设置

#### 1. Fork项目
点击GitHub页面右上角的"Fork"按钮

#### 2. 克隆代码
```bash
git clone https://github.com/your-username/xiangxin-guardrails.git
cd xiangxin-guardrails
```

#### 3. 设置上游仓库
```bash
git remote add upstream https://github.com/xiangxinai/xiangxin-guardrails.git
```

#### 4. 安装开发依赖

**后端开发环境：**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**前端开发环境：**
```bash
cd frontend
npm install
```

#### 5. 启动开发服务
```bash
# 启动后端（终端1）
cd backend
python main.py

# 启动前端（终端2）
cd frontend
npm run dev
```

### 开发流程

#### 1. 创建特性分支
```bash
git checkout -b feature/your-feature-name
# 或者修复分支
git checkout -b fix/your-bug-fix
```

#### 2. 进行开发
- 遵循现有代码风格
- 编写清晰的代码注释
- 添加适当的测试用例
- 确保代码通过现有测试

#### 3. 提交代码
```bash
git add .
git commit -m "feat: add new feature description"
# 或者
git commit -m "fix: fix bug description"
```

**提交信息格式：**
- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

#### 4. 推送到GitHub
```bash
git push origin feature/your-feature-name
```

#### 5. 创建Pull Request
1. 访问您fork的仓库页面
2. 点击"Compare & pull request"
3. 填写PR描述，说明：
   - 修改的内容和原因
   - 相关Issue编号
   - 测试方法
   - 截图（如有UI变更）

### 代码规范

#### Python代码规范
- 遵循PEP 8风格指南
- 使用black进行代码格式化
- 使用flake8进行代码检查
- 函数和类要有文档字符串

```python
def example_function(param1: str, param2: int) -> bool:
    """
    示例函数说明
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
        
    Returns:
        返回值说明
    """
    # 实现代码
    pass
```

#### TypeScript/React代码规范
- 使用ESLint和Prettier
- 使用TypeScript严格模式
- 组件要有PropTypes或TypeScript类型定义
- 使用函数式组件和Hooks

```typescript
interface Props {
  title: string;
  onClick: () => void;
}

const ExampleComponent: React.FC<Props> = ({ title, onClick }) => {
  return (
    <button onClick={onClick}>
      {title}
    </button>
  );
};
```

### 获得帮助

如果您需要帮助：

- 📧 发送邮件到：wanglei@xiangxinai.cn
- 💬 在GitHub Discussion中提问
- 🐛 在GitHub Issues中报告问题
- 📖 查看项目Wiki和文档

---

## English Version

### How to Contribute

We welcome the following types of contributions:

#### 🐛 Bug Reports
- Any issues encountered during usage
- Errors or inaccuracies in documentation
- Performance issues or abnormal behavior

#### 💡 Feature Suggestions
- Ideas and suggestions for new features
- Improvement suggestions for existing features
- User experience optimization suggestions

#### 📖 Documentation Improvements
- Fix documentation errors
- Add usage examples
- Translate documentation to other languages
- Improve code comments

#### 💻 Code Contributions
- Bug fixes
- New feature development
- Performance optimizations
- Adding test cases

### Development Environment Setup

#### 1. Fork the Project
Click the "Fork" button in the top right corner of the GitHub page

#### 2. Clone the Code
```bash
git clone https://github.com/your-username/xiangxin-guardrails.git
cd xiangxin-guardrails
```

#### 3. Set Up Upstream Repository
```bash
git remote add upstream https://github.com/xiangxinai/xiangxin-guardrails.git
```

#### 4. Install Development Dependencies

**Backend Development Environment:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend Development Environment:****
```bash
cd frontend
npm install
```

#### 5. Start Development Services
```bash
# Start backend (Terminal 1)
cd backend
python main.py

# Start frontend (Terminal 2)
cd frontend
npm run dev
```

### Development Workflow

#### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
# Or bug fix branch
git checkout -b fix/your-bug-fix
```

#### 2. Develop
- Follow existing code style
- Write clear code comments
- Add appropriate test cases
- Ensure code passes existing tests

#### 3. Commit Code
```bash
git add .
git commit -m "feat: add new feature description"
# Or
git commit -m "fix: fix bug description"
```

**Commit Message Format:**
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation updates
- `style:` Code formatting adjustments
- `refactor:` Code refactoring
- `test:` Test-related
- `chore:` Build process or auxiliary tool changes

#### 4. Push to GitHub
```bash
git push origin feature/your-feature-name
```

#### 5. Create Pull Request
1. Visit your forked repository page
2. Click "Compare & pull request"
3. Fill in PR description explaining:
   - What was changed and why
   - Related Issue numbers
   - Testing methods
   - Screenshots (if UI changes)

### Code Standards

#### Python Code Standards
- Follow PEP 8 style guide
- Use black for code formatting
- Use flake8 for code linting
- Functions and classes should have docstrings

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Example function description
    
    Args:
        param1: Parameter 1 description
        param2: Parameter 2 description
        
    Returns:
        Return value description
    """
    # Implementation code
    pass
```

#### TypeScript/React Code Standards
- Use ESLint and Prettier
- Use TypeScript strict mode
- Components should have PropTypes or TypeScript type definitions
- Use functional components and Hooks

```typescript
interface Props {
  title: string;
  onClick: () => void;
}

const ExampleComponent: React.FC<Props> = ({ title, onClick }) => {
  return (
    <button onClick={onClick}>
      {title}
    </button>
  );
};
```

### Getting Help

If you need help:

- 📧 Send email to: wanglei@xiangxinai.cn
- 💬 Ask questions in GitHub Discussion
- 🐛 Report issues in GitHub Issues
- 📖 Check project Wiki and documentation

---

*Thank you for contributing to making AI safer and more trustworthy!* 🙏