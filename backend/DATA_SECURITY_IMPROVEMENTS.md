# 数据安全功能改进总结

## 修改概述

本次修改主要解决了以下问题：

1. **系统默认实体类型命名规范化**：将系统自带的6个实体类型名称添加`_SYS`后缀
2. **租户级别的实体类型禁用功能**：允许租户禁用系统实体类型
3. **租户实体类型重名检查**：确保同一租户内实体类型不重名
4. **全局实体类型管理**：确保管理员对全局实体类型的修改影响所有租户

## 具体修改内容

### 1. 系统默认实体类型名称修改

**文件**: `backend/services/data_security_service.py`

将以下实体类型名称添加`_SYS`后缀：
- `ID_CARD_NUMBER` → `ID_CARD_NUMBER_SYS`
- `PHONE_NUMBER` → `PHONE_NUMBER_SYS`
- `EMAIL` → `EMAIL_SYS`
- `BANK_CARD_NUMBER` → `BANK_CARD_NUMBER_SYS`
- `PASSPORT_NUMBER` → `PASSPORT_NUMBER_SYS`
- `IP_ADDRESS` → `IP_ADDRESS_SYS`

### 2. 新增数据库表

**文件**: `backend/database/migrations/add_tenant_entity_type_disables.sql`

创建了`tenant_entity_type_disables`表，用于存储租户禁用的实体类型：
- `id`: 主键
- `tenant_id`: 租户ID
- `entity_type`: 被禁用的实体类型代码
- `disabled_at`: 禁用时间
- 唯一约束：`(tenant_id, entity_type)`

### 3. 新增数据库模型

**文件**: `backend/database/models.py`

添加了`TenantEntityTypeDisable`模型类，对应`tenant_entity_type_disables`表。

### 4. 数据安全服务增强

**文件**: `backend/services/data_security_service.py`

#### 新增方法：
- `disable_entity_type_for_tenant()`: 禁用租户的实体类型
- `enable_entity_type_for_tenant()`: 启用租户的实体类型
- `get_tenant_disabled_entity_types()`: 获取租户禁用的实体类型列表

#### 修改方法：
- `_get_user_entity_types()`: 在获取实体类型时排除被租户禁用的实体类型

### 5. API路由增强

**文件**: `backend/routers/data_security.py`

#### 新增API端点：
- `POST /api/v1/config/data-security/entity-types/{entity_type}/disable`: 禁用实体类型
- `POST /api/v1/config/data-security/entity-types/{entity_type}/enable`: 启用实体类型
- `GET /api/v1/config/data-security/disabled-entity-types`: 获取禁用的实体类型列表

#### 修改现有API：
- 创建实体类型时检查租户内重名（`create_entity_type`）

## 功能特性

### 1. 租户级别的实体类型管理

- **禁用系统实体类型**：租户可以禁用系统提供的实体类型，使其对自己不生效
- **启用系统实体类型**：租户可以重新启用之前禁用的系统实体类型
- **查看禁用状态**：租户可以查看当前禁用的实体类型列表

### 2. 实体类型重名检查

- **租户内唯一性**：同一租户内不能创建相同名称的实体类型
- **跨租户允许**：不同租户之间可以创建相同名称的实体类型

### 3. 全局实体类型管理

- **管理员权限**：只有超级管理员可以创建、修改、删除全局实体类型
- **全局影响**：管理员对全局实体类型的修改会立即影响所有租户
- **租户禁用**：租户可以禁用全局实体类型，但不影响其他租户

## 使用示例

### 1. 租户禁用系统实体类型

```bash
# 禁用身份证号检测
POST /api/v1/config/data-security/entity-types/ID_CARD_NUMBER_SYS/disable

# 禁用手机号检测
POST /api/v1/config/data-security/entity-types/PHONE_NUMBER_SYS/disable
```

### 2. 租户启用系统实体类型

```bash
# 启用身份证号检测
POST /api/v1/config/data-security/entity-types/ID_CARD_NUMBER_SYS/enable
```

### 3. 查看租户禁用的实体类型

```bash
GET /api/v1/config/data-security/disabled-entity-types

# 响应示例
{
    "disabled_entity_types": ["ID_CARD_NUMBER_SYS", "PHONE_NUMBER_SYS"]
}
```

## 数据库迁移

执行以下命令来应用数据库迁移：

```bash
cd backend
python -c "
from database.connection import get_db_session
from sqlalchemy import text

with open('database/migrations/add_tenant_entity_type_disables.sql', 'r') as f:
    sql = f.read()

db = get_db_session()
try:
    db.execute(text(sql))
    db.commit()
    print('Migration executed successfully')
except Exception as e:
    print(f'Migration failed: {e}')
    db.rollback()
finally:
    db.close()
"
```

## 注意事项

1. **向后兼容性**：现有的实体类型配置不会受到影响
2. **权限控制**：只有超级管理员可以管理全局实体类型
3. **数据一致性**：租户禁用实体类型不会影响其他租户
4. **性能考虑**：禁用检查在每次检测时都会执行，但查询效率较高

## 测试建议

1. **功能测试**：
   - 测试租户禁用/启用系统实体类型
   - 测试租户内实体类型重名检查
   - 测试管理员全局实体类型管理

2. **权限测试**：
   - 测试普通租户无法管理全局实体类型
   - 测试超级管理员可以管理全局实体类型

3. **数据一致性测试**：
   - 测试租户禁用不影响其他租户
   - 测试管理员修改全局实体类型影响所有租户
