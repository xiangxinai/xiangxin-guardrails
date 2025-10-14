# 数据库初始化指南

## 问题描述

在多个版本开发过程中，`/backend/database/migrations/` 目录下积累了大量SQL迁移文件。新用户首次启动Docker容器时，可能遇到数据库表结构不一致的问题，导致登录失败或其他错误。

## 解决方案

### 1. 自动化迁移系统

我们实现了一个自动化数据库迁移系统：

#### 核心组件

- **`database/run_migrations.py`**: 迁移执行脚本
- **`database/migrations/`**: SQL迁移文件目录
- **修改后的`database/connection.py`**: 在初始化时自动运行迁移

#### 工作原理

1. **迁移跟踪**: 系统创建`migration_history`表跟踪已执行的迁移
2. **幂等执行**: 每个迁移只执行一次，避免重复
3. **自动检测**: 启动时自动检测需要执行的迁移
4. **错误处理**: 迁移失败时有详细的错误日志和后备方案

### 2. 首次启动流程

#### 新用户部署步骤

1. **克隆代码仓库**
   ```bash
   git clone https://github.com/xiangxinai/xiangxin-guardrails.git
   cd xiangxin-guardrails
   ```

2. **配置环境变量** (可选)
   ```bash
   # 编辑 docker-compose.yml 中的环境变量
   # - 数据库密码
   # - 超级管理员账户
   # - API密钥等
   ```

3. **启动服务**
   ```bash
   docker compose up -d
   ```

4. **检查启动状态**
   ```bash
   docker compose logs admin-service | tail -20
   ```

#### 自动化过程

启动时，系统会按以下顺序执行：

1. **数据库连接检查**: 确保PostgreSQL服务就绪
2. **运行迁移**: 按预定义顺序执行所有需要的迁移脚本
3. **表结构同步**: SQLAlchemy确保所有模型表都已创建
4. **默认数据初始化**: 创建超级管理员和默认配置

### 3. 迁移文件管理

#### 迁移文件命名规范

- 使用描述性文件名：`add_feature_name.sql`
- 按时间顺序排序：旧迁移在前，新迁移在后
- 避免破坏性变更：优先使用ALTER TABLE而不是DROP/RECREATE

#### 添加新迁移

当需要添加新迁移时：

1. **创建迁移SQL文件**
   ```sql
   -- 新功能添加迁移示例
   ALTER TABLE tenants ADD COLUMN new_field VARCHAR(255) DEFAULT '';
   CREATE INDEX IF NOT EXISTS idx_tenants_new_field ON tenants(new_field);
   ```

2. **更新`run_migrations.py`中的迁移列表**
   ```python
   MIGRATION_FILES = [
       # ... 现有迁移
       "add_new_feature.sql",  # 添加到最后
   ]
   ```

3. **测试迁移**
   ```bash
   python3 backend/database/run_migrations.py
   ```

### 4. 故障排除

#### 常见问题

1. **迁移执行失败**
   ```
   错误: 迁移失败: add_feature.sql
   ```

   **解决方案**:
   - 检查SQL语法
   - 确保表存在性
   - 查看详细错误日志

2. **表结构不一致**
   ```
   错误: 列 'new_field' 不存在
   ```

   **解决方案**:
   - 手动执行缺失的迁移
   - 或设置`RESET_DATABASE_ON_STARTUP=true`重新初始化

3. **权限问题**
   ```
   错误: permission denied for table migration_history
   ```

   **解决方案**:
   - 确保数据库用户有足够的权限
   - 检查PostgreSQL连接配置

#### 手动重置数据库

如果需要完全重置数据库：

1. **停止服务**
   ```bash
   docker compose down
   ```

2. **删除数据库卷**
   ```bash
   docker volume rm xiangxin-guardrails_postgres_data
   ```

3. **重新启动**
   ```bash
   docker compose up -d
   ```

### 5. 开发环境建议

#### 最佳实践

1. **本地开发**: 使用`RESET_DATABASE_ON_STARTUP=true`快速重置
2. **测试环境**: 迁移测试脚本验证
3. **生产环境**: 先备份再执行迁移

#### 监控和维护

- 定期检查迁移状态
- 清理不需要的旧迁移文件
- 保持迁移文档更新

### 6. 迁移文件列表

当前系统包含以下迁移文件（按执行顺序）：

1. `rename_users_to_tenants.sql` - 用户表改名为租户表
2. `add_confidence_thresholds.sql` - 添加置信度阈值
3. `add_confidence_to_detection_results.sql` - 检测结果增加置信度
4. `add_confidence_trigger_level.sql` - 敏感度触发等级
5. `add_confidence_trigger_level_proxy.sql` - 代理服务敏感度配置
6. `add_stream_chunk_size.sql` - 流式响应块大小
7. `add_stream_chunk_size_to_proxy.sql` - 代理服务流式配置
8. `add_is_global_to_knowledge_bases.sql` - 知识库全局配置
9. `simplify_proxy_models.sql` - 简化代理模型结构
10. `add_data_security_fields.sql` - 数据安全字段
11. `add_data_security_tables.sql` - 数据安全表
12. `add_multimodal_fields.sql` - 多模态支持字段
13. `add_ban_policy_tables.sql` - 封禁策略表
14. `update_field_lengths.sql` - 字段长度优化
15. `cleanup_old_tables.sql` - 清理旧表
16. `migrate_to_english_fields.sql` - 字段国际化

### 7. 总结

新的自动化迁移系统确保了：

- ✅ 新用户首次启动时数据库结构正确
- ✅ 升级过程中平滑过渡
- ✅ 迁移过程的可靠性和可追踪性
- ✅ 开发和生产环境的一致性

通过这个系统，新用户可以直接使用`docker compose up -d`启动服务，系统会自动处理所有必要的数据库初始化和迁移工作。